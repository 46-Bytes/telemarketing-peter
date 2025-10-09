from datetime import datetime
from retell import Retell
import os
from dotenv import load_dotenv
import time
from config.database import get_prospects_collection
import logging
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

async def create_phone_call(prospects):
    """
    Initiate a phone call to one or more prospects
    
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
        
        phone_call_response = None
        
        counter = 0

        collection = get_prospects_collection()
        for prospect in prospects:
            counter += 1
            if not prospect.phoneNumber:
                prospect_name = prospect.name or "Unknown"
                logger.warning(f"Missing phone number for prospect {prospect_name}")
                continue
                
            # Log call initiation attempt
            prospect_name = prospect.name or "Unknown"
            logger.info(f"Initiating call to {prospect.phoneNumber} for {prospect_name}")
            logger.info(f"Campaign ID: {prospect.campaignId}")
            # Initiate the call
            phone_call_response = client.call.create_phone_call(
                from_number=from_number,
                to_number=prospect.phoneNumber,
                retell_llm_dynamic_variables={"user_name": prospect.name or "There", "business_name": prospect.businessName, "owner_name":prospect.ownerName,"phoneNumber":prospect.phoneNumber,"campaign_id":prospect.campaignId}
            )
            
            logger.info(f"Call initiated: {phone_call_response}")

            # Create audit log entry for call initiation
            audit_log = {
                "actionType": "Call Initiated",
                "performedBy": "AI Agent",
                "timestamp": {"$date": current_time},
                "details": {
                    "callId": phone_call_response.call_id,
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
                        "calls": {"callId": phone_call_response.call_id, "timestamp": current_time},
                        "auditLogs": audit_log
                    }
                }
            )
            time.sleep(1)
            if counter == 15:
                time.sleep(300)
                counter = 0

        return phone_call_response
    except Exception as e:
        logger.error(f"Error in create_phone_call: {str(e)}")
        raise

async def create_phone_call_background(prospects):
    """
    Background task version of create_phone_call that runs asynchronously
    
    Args:
        prospects (list): List of ProspectIn objects containing contact information
    """
    try:
        logger.info(f"Starting background phone call task for {len(prospects)} prospects")
        
        # Check if API key is available
        api_key = os.getenv("RETELL_API_KEY")
        if not api_key:
            logger.error("RETELL_API_KEY environment variable not set")
            return
            
        # Check if from number is available
        from_number = os.getenv("FROM_NUMBER")
        if not from_number:
            logger.error("FROM_NUMBER environment variable not set")
            return
            
        client = Retell(api_key=api_key)
        current_time = datetime.utcnow().isoformat() + "Z"
        
        if not prospects or len(prospects) == 0:
            logger.warning("No prospects provided for call initiation")
            return
        
        collection = get_prospects_collection()
        counter = 0
        
        for prospect in prospects:
            counter += 1
            if not prospect.phoneNumber:
                prospect_name = prospect.name or "Unknown"
                logger.warning(f"Missing phone number for prospect {prospect_name}")
                continue
                
            # Log call initiation attempt
            prospect_name = prospect.name or "Unknown"
            logger.info(f"[Background] Initiating call to {prospect.phoneNumber} for {prospect_name}")
            logger.info(f"[Background] Campaign ID: {prospect.campaignId}")
            
            try:
                # Initiate the call
                phone_call_response = client.call.create_phone_call(
                    from_number=from_number,
                    to_number=prospect.phoneNumber,
                    retell_llm_dynamic_variables={
                        "user_name": prospect.name or "There", 
                        "business_name": prospect.businessName, 
                        "owner_name": prospect.ownerName,
                        "phoneNumber": prospect.phoneNumber,
                        "campaign_id": prospect.campaignId
                    }
                )
                
                logger.info(f"[Background] Call initiated: {phone_call_response}")

                # Create audit log entry for call initiation
                audit_log = {
                    "actionType": "Call Initiated (Background)",
                    "performedBy": "AI Agent",
                    "timestamp": {"$date": current_time},
                    "details": {
                        "callId": phone_call_response.call_id,
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
                            "calls": {"callId": phone_call_response.call_id, "timestamp": current_time},
                            "auditLogs": audit_log
                        }
                    }
                )
                
                # Add delay between calls
                await asyncio.sleep(1)
                
                # Rate limiting: sleep for 5 minutes after every 15 calls
                if counter == 15:
                    logger.info("[Background] Rate limiting: sleeping for 5 minutes after 15 calls")
                    await asyncio.sleep(300)  # 5 minutes
                    counter = 0
                    
            except Exception as call_error:
                logger.error(f"[Background] Error initiating call to {prospect.phoneNumber}: {str(call_error)}")
                continue
                
        logger.info(f"[Background] Completed phone call task for {len(prospects)} prospects")
        
    except Exception as e:
        logger.error(f"[Background] Error in create_phone_call_background: {str(e)}")
        raise