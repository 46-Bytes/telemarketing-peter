"""
Auto Retry Scheduler - Processes automatic call retries for prospects who didn't pick up.

This scheduler runs periodically to find prospects that are scheduled for automatic retry
and initiates calls to them.
"""

from datetime import datetime
from services.auto_retry_service import get_prospects_for_auto_retry
from services.call_initiation_service import create_phone_call
from models.prospect import ProspectIn
import logging
import asyncio
from utils.timezone import get_brisbane_date, get_brisbane_time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def process_auto_retries():
    """
    Main function to process automatic retries for prospects who didn't pick up.

    This function:
    1. Finds prospects scheduled for auto-retry
    2. Initiates calls to them
    3. The webhook will handle scheduling the next retry or sending failure email
    """
    try:
        current_date = get_brisbane_date()
        current_time = get_brisbane_time()

        # Get prospects due for auto-retry
        prospects, candidates_today = get_prospects_for_auto_retry()

        # Summary line
        logger.info("[SCHEDULER] Auto-Retries — Automatic retries for prospects who didn't pick up | time=%s | date=%s | candidates_today=%d | matched_now=%d",
                     current_time, current_date, len(candidates_today), len(prospects))

        # Log all auto-retry candidates for today
        matched_phones = {p.get("phoneNumber") for p in prospects}
        for p in candidates_today:
            marker = " << CALLING NOW" if p.get("phoneNumber") in matched_phones else ""
            logger.info("  -> name=%s | phone=%s | campaignId=%s | time=%s%s",
                         p.get("name", "Unknown"),
                         p.get("phoneNumber", "N/A"),
                         p.get("campaignId", "N/A"),
                         p.get("autoRetryScheduledTime", "N/A"),
                         marker)

        if not prospects:
            return

        # Convert MongoDB documents to ProspectIn objects
        prospect_objects = []
        for prospect in prospects:
            try:
                prospect_obj = ProspectIn(
                    name=prospect.get("name"),
                    phoneNumber=prospect["phoneNumber"],
                    businessName=prospect.get("businessName", ""),
                    ownerName=prospect.get("ownerName", ""),
                    campaignId=prospect.get("campaignId"),
                    campaignName=prospect.get("campaignName"),
                    isCallBack=True,
                    callBackDate=prospect.get("autoRetryScheduledDate"),
                    callBackTime=prospect.get("autoRetryScheduledTime")
                )
                prospect_objects.append(prospect_obj)
            except Exception as e:
                logger.error(f"Error preparing prospect for auto-retry: {str(e)}")
                continue

        if not prospect_objects:
            return

        logger.info("[CALL] Auto-retry starting | count=%s", len(prospect_objects))
        try:
            result = await create_phone_call(prospect_objects, source="auto_retry")
        except Exception as call_error:
            logger.error("[CALL] Auto-retry failed: %s", call_error)
            raise

    except Exception as e:
        logger.error(f"Error in process_auto_retries: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    # For testing purposes
    asyncio.run(process_auto_retries())
