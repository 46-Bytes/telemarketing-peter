from datetime import datetime
from retell import Retell
import os
from dotenv import load_dotenv
import time
from config.database import get_prospects_collection
import logging
from typing import List, Dict, Any
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def is_valid_number(phone_number: str) -> bool:
    """
    Validate Australian and Pakistani phone number format using regex.
    
    Valid formats:
    - +61XXXXXXXXX (11 digits total, +61 + 9 digits) - Australian
    - 0XXXXXXXXX (10 digits starting with 0) - Australian
    - XXXXXXXXX (9 digits) - Australian
    - +92XXXXXXXXX (12 digits total, +92 + 10 digits) - Pakistani
    
    Args:
        phone_number (str): Phone number to validate
        
    Returns:
        bool: True if valid Australian or Pakistani phone number, False otherwise
    """
    if not phone_number:
        return False
    
    # Remove any spaces, dashes, parentheses, and other non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone_number.strip())
    
    # Australian and Pakistani phone number patterns
    patterns = [
        r'^\+61[2-9]\d{8}$',  # +61 followed by 9 digits (mobile/landline) - Australian
        r'^\+92[3-9]\d{9}$',  # +92 followed by 10 digits (mobile) - Pakistani
    ]
    
    for pattern in patterns:
        if re.match(pattern, cleaned):
            return True
    
    return False

async def create_phone_call(prospects):
    """
    Initiate phone calls to prospects using batch calls for efficiency
    
    Args:
        prospects (list): List of ProspectIn objects containing contact information
        
    Returns:
        dict: Result of the call initiation
    """
    try:
        # Check if API key is available
        api_key = os.getenv("RETELL_API_KEY")
        if not api_key:
            raise ValueError("RETELL_API_KEY environment variable not set")
            
        # Check if from number is available
        from_number = os.getenv("FROM_NUMBER")
        if not from_number:
            raise ValueError("FROM_NUMBER environment variable not set")
            
        client = Retell(api_key=api_key)
        current_time = datetime.utcnow().isoformat() + "Z"
        
        if not prospects or len(prospects) == 0:
            raise ValueError("No prospects provided for call initiation")
        
        # Filter out prospects without phone numbers
        valid_prospects = [p for p in prospects if p.phoneNumber]
        if not valid_prospects:
            logger.warning("No valid prospects with phone numbers found")
            return None
            
        logger.info(f"Processing {len(valid_prospects)} prospects for batch calls")
        
        # Initialize campaign report if campaign_id is available
        if valid_prospects and hasattr(valid_prospects[0], 'campaignId') and valid_prospects[0].campaignId:
            campaign_id = valid_prospects[0].campaignId
            logger.info(f"Initializing campaign report for campaign {campaign_id}")
            try:
                from services.report_service import seed_rows_if_missing
                prospects_data = [
                    {
                        "name": p.name or "",
                        "phoneNumber": p.phoneNumber,
                        "businessName": p.businessName or "",
                    }
                    for p in valid_prospects
                ]
                seed_rows_if_missing(campaign_id, prospects_data)
                logger.info(f"Campaign report initialized for {len(prospects_data)} prospects")
            except Exception as report_error:
                logger.warning(f"Failed to initialize campaign report: {str(report_error)}")
        
        # Batch size for Retell (concurrency of 15)
        BATCH_SIZE = 15
        total_batches = (len(valid_prospects) + BATCH_SIZE - 1) // BATCH_SIZE
        
        collection = get_prospects_collection()
        batch_responses = []
        
        # Process prospects in batches
        for batch_num in range(total_batches):
            start_idx = batch_num * BATCH_SIZE
            end_idx = min(start_idx + BATCH_SIZE, len(valid_prospects))
            batch_prospects = valid_prospects[start_idx:end_idx]
            
            logger.info(f"Processing batch {batch_num + 1}/{total_batches} with {len(batch_prospects)} prospects")
            
            # Prepare batch call tasks
            tasks = []
            prospect_mapping = {}  # Map phone numbers to prospect objects for database updates
            
            for prospect in batch_prospects:
                prospect_name = prospect.name or "Unknown"
                
                # Validate phone number before adding to batch
                if not is_valid_number(prospect.phoneNumber):
                    logger.warning(f"Invalid phone number for {prospect_name}: {prospect.phoneNumber} - Skipping prospect")
                    continue
                
                logger.info(f"Adding to batch: {prospect.phoneNumber} for {prospect_name}")
                
                # Create task for batch call
                # If this is a callback, include latest transcript/summary for context
                previous_transcript = None
                previous_summary = None
                is_callback_flag = False
                email_for_call = None
                try:
                    db_prospect = collection.find_one({"phoneNumber": prospect.phoneNumber, "campaignId": getattr(prospect, "campaignId", None)})
                    is_callback_flag = getattr(prospect, "isCallBack", None)
                    if db_prospect:
                        if is_callback_flag is None:
                            is_callback_flag = db_prospect.get("isCallBack")
                        if is_callback_flag is True:
                            calls = db_prospect.get("calls", [])
                            if isinstance(calls, list) and len(calls) > 0:
                                # Find the most recent call that has a transcript (skip pending calls)
                                # Iterate backwards to find the latest completed call with transcript
                                for call in reversed(calls):
                                    call_transcript = call.get("transcript")
                                    call_summary = call.get("callSummary")
                                    # Use the first call we find with either transcript or summary
                                    if call_transcript or call_summary:
                                        previous_transcript = call_transcript
                                        previous_summary = call_summary
                                        logger.info(f"Found previous call context for callback - transcript length: {len(call_transcript) if call_transcript else 0}, summary: {call_summary[:100] if call_summary else 'None'}...")
                                        break
                                if not previous_transcript and not previous_summary:
                                    logger.warning(f"No previous transcript or summary found for callback to {prospect.phoneNumber}")
                        # Prefer email coming from UI/prospect object; fall back to stored DB email
                        email_for_call = getattr(prospect, "email", None) or db_prospect.get("email")
                except Exception as _cb_e:
                    logger.warning(f"Could not enrich callback context for {prospect.phoneNumber}: {_cb_e}")
                    # Fallback: still try to use email from the incoming prospect if available
                    email_for_call = getattr(prospect, "email", None)

                # Convert is_callback_flag to string (API requires string, not boolean)
                is_callback_str = "true" if is_callback_flag is True else "false"
                
                # Ensure previous_transcript and previous_summary are strings (API requires strings, not None)
                previous_transcript_str = previous_transcript if previous_transcript is not None else ""
                previous_summary_str = previous_summary if previous_summary is not None else ""

                task = {
                    "to_number": prospect.phoneNumber,
                    "retell_llm_dynamic_variables": {
                        "user_name": prospect.name or "There",
                        "business_name": prospect.businessName,
                        "owner_name": prospect.ownerName,
                        "phoneNumber": prospect.phoneNumber,
                        "campaign_id": prospect.campaignId,
                        "email": email_for_call or "",
                        "is_callback": is_callback_str,
                        "previous_transcript": previous_transcript_str,
                        "previous_summary": previous_summary_str
                    }
                }
                tasks.append(task)
                prospect_mapping[prospect.phoneNumber] = prospect
                logger.info(f"Task created for {prospect.phoneNumber}: {task}")
            
            try:
                # Create batch call
                batch_response = client.batch_call.create_batch_call(
                    from_number=from_number,
                    tasks=tasks
                )
                
                logger.info(f"Batch {batch_num + 1} initiated successfully: {batch_response}")
                batch_responses.append(batch_response)
                
                # Update database for each prospect in this batch
                for prospect in batch_prospects:
                    # Create audit log entry for call initiation
                    audit_log = {
                        "actionType": "Batch Call Initiated",
                        "performedBy": "AI Agent",
                        "timestamp": {"$date": current_time},
                        "details": {
                            "batchId": batch_response.batch_call_id,
                            "status": "Initiated"
                        }
                    }

                    # Update the prospect in the database
                    collection.update_one(
                        {"phoneNumber": prospect.phoneNumber, "campaignId": prospect.campaignId},
                        {
                            "$set": {"status": "contacted"},
                            "$inc": {"retryCount": 1},
                            "$push": {
                                "calls": {"batchId": batch_response.batch_call_id, "timestamp": current_time},
                                "auditLogs": audit_log
                            }
                        }
                    )
                
                # Add delay between batches to avoid overwhelming the system
                if batch_num < total_batches - 1:  # Don't sleep after the last batch
                    logger.info(f"Waiting 2 seconds before next batch...")
                    time.sleep(2)
                    
            except Exception as batch_error:
                logger.error(f"Error in batch {batch_num + 1}: {str(batch_error)}")
                # Continue with next batch even if one fails
                continue
        
        logger.info(f"Completed processing {len(valid_prospects)} prospects in {total_batches} batches")
        return {
            "total_prospects": len(valid_prospects),
            "total_batches": total_batches,
            "batch_responses": batch_responses
        }
        
    except Exception as e:
        logger.error(f"Error in create_phone_call: {str(e)}")
        raise


def update_batch_call_status(batch_id: str, call_results: List[Dict[str, Any]]):
    """
    Update prospect statuses based on batch call results
    
    Args:
        batch_id (str): The batch ID from Retell
        call_results (list): List of call results from Retell batch call
    """
    try:
        collection = get_prospects_collection()
        current_time = datetime.utcnow().isoformat() + "Z"
        
        for call_result in call_results:
            phone_number = call_result.get('to_number')
            call_id = call_result.get('call_id')
            call_status = call_result.get('status', 'unknown')
            
            if not phone_number or not call_id:
                logger.warning(f"Invalid call result: {call_result}")
                continue
            
            # Extract all call details from webhook
            duration_ms = call_result.get('duration_ms', 0)
            duration_seconds = duration_ms / 1000 if duration_ms else 0
            
            # Get additional call details
            transcript = call_result.get('transcript', '')
            call_summary = call_result.get('call_summary', '')
            recording_url = call_result.get('recording_url', '')
            start_timestamp = call_result.get('start_timestamp', 0)
            
            # Convert timestamp to ISO format
            call_timestamp = datetime.fromtimestamp(start_timestamp / 1000).isoformat() + "Z" if start_timestamp else current_time
            
            # Determine prospect status based on call status
            if call_status == 'ended':
                prospect_status = 'picked_up'
            elif call_status in ['busy', 'no_answer', 'voicemail']:
                prospect_status = 'contacted'  # Keep as contacted for retry
            else:
                prospect_status = 'error'
            
            # Create comprehensive call info object
            call_info = {
                "callId": call_id,
                "batchId": batch_id,
                "timestamp": call_timestamp,
                "duration": duration_seconds,
                "status": call_status,
                "recordingUrl": recording_url,
                "transcript": transcript,
                "callSummary": call_summary
            }
            
            # Create audit log entry
            audit_log = {
                "actionType": "Batch Call Completed",
                "performedBy": "AI Agent",
                "timestamp": {"$date": current_time},
                "details": {
                    "batchId": batch_id,
                    "callId": call_id,
                    "status": call_status,
                    "duration": duration_seconds
                }
            }
            
            # Update prospect in database - replace the existing call entry with batchId
            update_result = collection.update_one(
                {
                    "phoneNumber": phone_number,
                    "calls.batchId": batch_id
                },
                {
                    "$set": {
                        "status": prospect_status,
                        "calls.$": call_info,  # Replace the entire call object
                        "updatedAt": {"$date": current_time}
                    },
                    "$push": {
                        "auditLogs": audit_log
                    }
                }
            )
            
            if update_result.modified_count > 0:
                logger.info(f"Updated prospect {phone_number} with status {prospect_status}, call_id: {call_id}")
            else:
                # If no prospect found with batchId, try to find by phone number and add call
                logger.warning(f"No prospect found with batch ID {batch_id} for phone {phone_number}, trying to add call directly")
                
                # Find prospect by phone number and add call
                prospect = collection.find_one({"phoneNumber": phone_number})
                if prospect:
                    collection.update_one(
                        {"phoneNumber": phone_number},
                        {
                            "$set": {"status": prospect_status},
                            "$push": {
                                "calls": call_info,
                                "auditLogs": audit_log
                            },
                            "$inc": {"retryCount": 1}
                        }
                    )
                    logger.info(f"Added call to prospect {phone_number} directly")
                else:
                    logger.error(f"No prospect found for phone number {phone_number}")
                
    except Exception as e:
        logger.error(f"Error updating batch call status: {str(e)}")
        raise


def get_batch_call_status(batch_id: str):
    """
    Get the status of a batch call from Retell
    
    Args:
        batch_id (str): The batch ID from Retell
        
    Returns:
        dict: Batch call status and results
    """
    try:
        api_key = os.getenv("RETELL_API_KEY")
        if not api_key:
            raise ValueError("RETELL_API_KEY environment variable not set")
            
        client = Retell(api_key=api_key)
        
        # Get batch call status
        batch_status = client.batch_call.get_batch_call(batch_id)
        
        logger.info(f"Batch {batch_id} status: {batch_status}")
        return batch_status
        
    except Exception as e:
        logger.error(f"Error getting batch call status: {str(e)}")
        raise