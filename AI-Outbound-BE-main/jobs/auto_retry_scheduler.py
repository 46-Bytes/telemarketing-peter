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
        logger.info("=" * 80)
        logger.info("Starting auto-retry processing...")
        logger.info("=" * 80)
        
        # Get prospects due for auto-retry
        prospects = get_prospects_for_auto_retry()
        
        if not prospects:
            logger.info("No prospects found for auto-retry at this time")
            return
        
        logger.info(f"Processing {len(prospects)} prospects for auto-retry")
        
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
                    # Mark this as a callback so the AI has context from previous calls
                    isCallBack=True,
                    callBackDate=prospect.get("autoRetryScheduledDate"),
                    callBackTime=prospect.get("autoRetryScheduledTime")
                )
                prospect_objects.append(prospect_obj)
                
                logger.info(
                    f"Prepared auto-retry for: {prospect.get('name', 'Unknown')} "
                    f"({prospect['phoneNumber']}) - Attempt #{prospect.get('autoRetryCount', 0)}"
                )
            except Exception as e:
                logger.error(f"Error preparing prospect for auto-retry: {str(e)}")
                continue
        
        if not prospect_objects:
            logger.warning("No valid prospects prepared for auto-retry")
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


