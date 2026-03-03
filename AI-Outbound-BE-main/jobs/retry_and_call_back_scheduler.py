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
    """Fetch prospects that need callback based on criteria.
    Returns (matched_prospects, candidates_today_count)."""
    try:
        collection = get_prospects_collection()

        current_date = get_brisbane_date()
        current_time_hm = get_brisbane_time()

        query = {
            "$and": [
                {"status": {"$ne": "new"}},
                {"isCallBack": True},
                {"callBackDate": {"$eq": current_date}}
            ]
        }

        candidates = list(collection.find(query))

        # Apply time filter: only include when callBackTime matches current time exactly
        prospects = []
        for p in candidates:
            cb_time = p.get("callBackTime")
            if cb_time and isinstance(cb_time, str) and len(cb_time) in (4, 5):
                try:
                    parts = cb_time.split(":")
                    cb_time_norm = f"0{parts[0]}:{parts[1]}" if len(parts[0]) == 1 else cb_time
                    if cb_time_norm == current_time_hm:
                        prospects.append(p)
                except Exception as e:
                    logger.error(f"Error parsing callback time for prospect {p.get('phoneNumber', 'N/A')}: {str(e)}")

        return prospects, len(candidates)

    except Exception as e:
        logger.error(f"Error fetching prospects for callback: {str(e)}")
        raise

async def schedule_callbacks():
    """Main function to schedule callbacks for prospects"""
    try:
        current_date = get_brisbane_date()
        current_time = get_brisbane_time()

        prospects, candidates_today = get_prospects_for_callback()

        # Summary line
        logger.info("[SCHEDULER] Callbacks | time=%s | date=%s | candidates_today=%d | matched_now=%d",
                     current_time, current_date, candidates_today, len(prospects))

        if not prospects:
            return

        # Log each prospect that will be called back
        for p in prospects:
            logger.info("  -> %s | %s | %s | campaign=%s | callback=%s %s",
                         p.get("name", "Unknown"),
                         p.get("phoneNumber", "N/A"),
                         p.get("businessName", "N/A"),
                         p.get("campaignId", "N/A"),
                         p.get("callBackDate", "N/A"),
                         p.get("callBackTime", "N/A"))

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

        logger.info("[CALL] Callback scheduler starting | count=%s", len(prospect_objects))
        result = await create_phone_call(prospect_objects, source="callback")

    except Exception as e:
        logger.error(f"Error in schedule_callbacks: {str(e)}", exc_info=True)
        raise
