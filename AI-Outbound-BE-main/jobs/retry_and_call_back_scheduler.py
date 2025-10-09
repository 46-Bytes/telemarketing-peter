from datetime import datetime, timedelta
from services.prospect_service import get_prospects_collection
from services.call_initiation_service import create_phone_call_background
from models.prospect import ProspectIn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_prospects_for_callback():
    """Fetch prospects that need callback based on criteria"""
    try:
        collection = get_prospects_collection()
        
        # Get current date in YYYY/MM/DD format
        current_date = datetime.utcnow().strftime("%Y-%m-%d")
        
        # Query to find prospects that need callback
        query = {
            "$and": [
                {"retryCount": {"$gt": 0, "$lt": 4}},
                {"status": {"$ne": "new"}},
                {"callBackCount": {"$lt" : 3}},
                {
                    "$or": [
                        {"callBackDate": {"$eq": current_date}}
                    ]
                }
            ]
        }

        prospects = list(collection.find(query))

        logger.info(f"Found {len(prospects)} prospects for callback  245")
        return prospects

    except Exception as e:
        logger.error(f"Error fetching prospects for callback: {str(e)}")
        raise

async def schedule_callbacks():
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
                # scheduledCallDate=datetime.fromisoformat(prospect["scheduledCallDate"].replace("Z", "+00:00"))
            ) for prospect in prospects
        ]

        # Initiate calls in background
        logger.info(f"@@@@ -- call Scheduler------  Initiating calls for {len(prospect_objects)} prospects")
        await create_phone_call_background(prospect_objects)

    except Exception as e:
        logger.error(f"Error in schedule_callbacks: {str(e)}")
        raise 