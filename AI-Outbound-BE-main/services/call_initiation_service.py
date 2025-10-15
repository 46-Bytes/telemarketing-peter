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

def is_valid_australian_phone(phone_number: str) -> bool:
    """
    Validate Australian phone number format using regex.
    
    Valid formats:
    - +61XXXXXXXXX (11 digits total, +61 + 9 digits)
    - 0XXXXXXXXX (10 digits starting with 0)
    - XXXXXXXXX (9 digits)
    
    Args:
        phone_number (str): Phone number to validate
        
    Returns:
        bool: True if valid Australian phone number, False otherwise
    """
    if not phone_number:
        return False
    
    # Remove any spaces, dashes, parentheses, and other non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone_number.strip())
    
    # Australian phone number patterns
    patterns = [
        r'^\+61[2-9]\d{8}$',  # +61 followed by 9 digits (mobile/landline)
    ]
    
    for pattern in patterns:
        if re.match(pattern, cleaned):
            return True
    
    return False

def create_phone_call(prospects):
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
                if not is_valid_australian_phone(prospect.phoneNumber):
                    logger.warning(f"Invalid phone number for {prospect_name}: {prospect.phoneNumber} - Skipping prospect")
                    continue
                
                logger.info(f"Adding to batch: {prospect.phoneNumber} for {prospect_name}")
                
                # Create task for batch call
                task = {
                    "to_number": prospect.phoneNumber,
                    "retell_llm_dynamic_variables": {
                        "user_name": prospect.name or "There",
                        "business_name": prospect.businessName,
                        "owner_name": prospect.ownerName,
                        "phoneNumber": prospect.phoneNumber,
                        "campaign_id": prospect.campaignId
                    }
                }
                tasks.append(task)
                prospect_mapping[prospect.phoneNumber] = prospect
            
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