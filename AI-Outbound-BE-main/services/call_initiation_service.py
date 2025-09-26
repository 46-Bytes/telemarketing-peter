from datetime import datetime
from retell import Retell
import os
from dotenv import load_dotenv
import time
from config.database import get_prospects_collection
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def create_phone_call(prospects):
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
        
        collection = get_prospects_collection()
        for prospect in prospects:
            if not prospect.phoneNumber:
                logger.warning(f"Missing phone number for prospect {prospect.name}")
                continue
                
            # Log call initiation attempt
            logger.info(f"Initiating call to {prospect.phoneNumber} for {prospect.name}")
            logger.info(f"Campaign ID: {prospect.campaignId}")
            # Initiate the call
            phone_call_response = client.call.create_phone_call(
                from_number=from_number,
                to_number=prospect.phoneNumber,
                retell_llm_dynamic_variables={"user_name": prospect.name, "business_name": prospect.businessName, "owner_name":prospect.ownerName,"phoneNumber":prospect.phoneNumber,"campaign_id":prospect.campaignId}
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

        return phone_call_response
    except Exception as e:
        logger.error(f"Error in create_phone_call: {str(e)}")
        raise