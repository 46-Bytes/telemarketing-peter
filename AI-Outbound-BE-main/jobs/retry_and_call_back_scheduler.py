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
                {"retryCount": {"$gt": 0, "$lt": 4}},
                {"status": {"$ne": "new"}},
                {"callBackCount": {"$lt" : 3}},
                {"isCallBack": True},
                {
                    "$or": [
                        {"callBackDate": {"$eq": current_date}}
                    ]
                }
            ]
        }

        candidates = list(collection.find(query))

        # Apply time filter: if callBackTime exists (HH:MM), only include when time <= now
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
                    if cb_time_norm <= current_time_hm:
                        prospects.append(p)
                except Exception:
                    prospects.append(p)
            else:
                prospects.append(p)

        logger.info(f"Found {len(prospects)} prospects for callback  245")
        return prospects

    except Exception as e:
        logger.error(f"Error fetching prospects for callback: {str(e)}")
        raise

def schedule_callbacks():
    """Main function to schedule callbacks for prospects"""
    try:
        # Get prospects that need callback
        prospects = get_prospects_for_callback()
        
        if not prospects:
            logger.info("No prospects found for callback")
            return

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

        # Initiate calls
        logger.info(f"@@@@ -- call Scheduler------  Initiating calls for {len(prospect_objects)} prospects")
        create_phone_call(prospect_objects)

    except Exception as e:
        logger.error(f"Error in schedule_callbacks: {str(e)}")
        raise 