from datetime import datetime, timedelta
from services.prospect_service import get_prospects_collection
from services.call_initiation_service import create_phone_call
from models.prospect import ProspectIn
import logging
from utils.timezone import get_brisbane_date, get_brisbane_time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_prospects_for_callback():
    """Fetch prospects that need callback based on criteria"""
    try:
        collection = get_prospects_collection()
        
        # Brisbane-local date and time
        current_date = get_brisbane_date()
        current_time_hm = get_brisbane_time()
        
        # Query to find prospects that need callback
        query = {
            "$and": [
                # {"retryCount": {"$gt": 0, "$lt": 4}},
                {"status": {"$ne": "new"}},
                # {"callBackCount": {"$lt" : 3}},
                {"isCallBack": True},
                {
                    "$or": [
                        {"callBackDate": {"$eq": current_date}}
                    ]
                }
            ]
        }

        candidates = list(collection.find(query))
        logger.info(f"Found {len(candidates)} candidates for callback on {current_date}")

        # Apply time filter: if callBackTime exists (HH:MM), only include when time matches exactly
        prospects = []
        for p in candidates:
            cb_time = p.get("callBackTime")
            if cb_time and isinstance(cb_time, str) and len(cb_time) in (4, 5):
                try:
                    parts = cb_time.split(":")
                    if len(parts[0]) == 1:
                        cb_time_norm = f"0{parts[0]}:{parts[1]}"
                    else:
                        cb_time_norm = cb_time
                    # Only match exact time to prevent duplicate calls
                    if cb_time_norm == current_time_hm:
                        prospects.append(p)
                        logger.info(f"✓ Callback time match - Prospect: {p.get('name', 'Unknown')}, Phone: {p.get('phoneNumber', 'N/A')}, Time: {cb_time_norm}")
                    else:
                        logger.debug(f"✗ Callback time mismatch - Prospect: {p.get('name', 'Unknown')}, Callback time: {cb_time_norm}, Current time: {current_time_hm}")
                except Exception as e:
                    logger.error(f"Error parsing callback time for prospect {p.get('phoneNumber', 'N/A')}: {str(e)}")
                    # Don't add prospects with invalid time formats to avoid unintended calls
            else:
                # If no callback time specified, include the prospect (backward compatibility)
                # prospects.append(p)
                logger.info(f"✓ Callback without specific time - Prospect: {p.get('name', 'Unknown')}, Phone: {p.get('phoneNumber', 'N/A')}")

        logger.info(f"Found {len(prospects)} prospects for callback")
        return prospects

    except Exception as e:
        logger.error(f"Error fetching prospects for callback: {str(e)}")
        raise

async def schedule_callbacks():
    """Main function to schedule callbacks for prospects"""
    try:
        # Get prospects that need callback (with exact time matching to prevent duplicates)
        prospects = get_prospects_for_callback()
        
        if not prospects:
            logger.info("No prospects found for callback")
            return

        logger.info(f"Processing {len(prospects)} prospects for callback")

        # Convert MongoDB documents to ProspectIn objects
        prospect_objects = [
            ProspectIn(
                name=prospect.get("name"),
                phoneNumber=prospect["phoneNumber"],
                businessName=prospect["businessName"],
                ownerName=prospect.get("ownerName", ""),
                campaignId=prospect.get("campaignId"),
                campaignName=prospect.get("campaignName"),
                isCallBack=True,
                callBackDate=prospect.get("callBackDate"),
                callBackTime=prospect.get("callBackTime"),
            ) for prospect in prospects
        ]

        # Log prospect details before initiating calls
        for po in prospect_objects:
            logger.info(f"Initiating callback for: {po.name} ({po.phoneNumber}) at {po.callBackTime}")

        # Initiate calls
        logger.info(f"@@@@ -- Callback Scheduler ------  Initiating callback calls for {len(prospect_objects)} prospects")
        result = await create_phone_call(prospect_objects)
        logger.info(f"@@@@ -- Callback Scheduler ------  Callback initiation completed. Result: {result}")

    except Exception as e:
        logger.error(f"Error in schedule_callbacks: {str(e)}", exc_info=True)
        raise 