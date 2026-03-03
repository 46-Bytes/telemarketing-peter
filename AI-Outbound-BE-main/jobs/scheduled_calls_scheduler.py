from datetime import datetime, timedelta
from services.prospect_service import get_prospects_collection
from services.call_initiation_service import create_phone_call
from services.report_service import seed_rows_if_missing
from models.prospect import ProspectIn
import logging
from utils.timezone import get_brisbane_now, get_brisbane_date, get_brisbane_time, is_within_call_hours, get_brisbane_timezone_info

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_scheduled_prospects():
    """Fetch prospects that are scheduled for calls today"""
    try:
        collection = get_prospects_collection()
        current_date = get_brisbane_date()

        query = {
            "scheduledCallDate": {"$regex": f"^{current_date}"},
            "status": "new"
        }

        prospects = list(collection.find(query))
        return prospects

    except Exception as e:
        logger.error(f"Error fetching scheduled prospects: {str(e)}")
        raise

# Note: is_within_call_hours() is now imported from utils.timezone

async def process_scheduled_calls():
    """Main function to process scheduled calls"""
    try:
        current_date = get_brisbane_date()
        current_time = get_brisbane_time()

        # Check if current time is within allowed call hours in Brisbane timezone
        if not is_within_call_hours():
            logger.info("[SCHEDULER] Scheduled Calls | time=%s | outside call hours (8AM-6PM) — skipped", current_time)
            return

        # Get prospects scheduled for today
        all_today = get_scheduled_prospects()

        # Filter by exact time match
        prospects_to_call = [
            p for p in all_today
            if p.get("scheduledCallTime", "") == current_time
        ]

        # Summary line
        logger.info("[SCHEDULER] Scheduled Calls | time=%s | date=%s | today_total=%d | matched_now=%d",
                     current_time, current_date, len(all_today), len(prospects_to_call))

        if not prospects_to_call:
            return

        # Log each prospect that will be called
        for p in prospects_to_call:
            logger.info("  -> %s | %s | %s | campaign=%s | scheduled=%s",
                         p.get("name", "Unknown"),
                         p.get("phoneNumber", "N/A"),
                         p.get("businessName", "N/A"),
                         p.get("campaignId", "N/A"),
                         p.get("scheduledCallTime", "N/A"))

        # Convert MongoDB documents to ProspectIn objects
        prospect_objects = [
            ProspectIn(
                name=prospect.get("name"),
                phoneNumber=prospect["phoneNumber"],
                businessName=prospect["businessName"],
                scheduledCallDate=datetime.fromisoformat(prospect["scheduledCallDate"].replace("Z", "+00:00")),
                ownerName=prospect.get("ownerName", ""),
                campaignId=prospect.get("campaignId", ""),
                scheduledCallTime=prospect.get("scheduledCallTime", "")
            ) for prospect in prospects_to_call
        ]

        logger.info("[CALL] Scheduled calls starting | count=%s", len(prospect_objects))
        await create_phone_call(prospect_objects, source="scheduled")

    except Exception as e:
        logger.error(f"Error in process_scheduled_calls: {str(e)}")
        raise
