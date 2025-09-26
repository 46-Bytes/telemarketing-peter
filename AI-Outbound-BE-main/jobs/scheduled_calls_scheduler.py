from datetime import datetime, timedelta
from services.prospect_service import get_prospects_collection
from services.call_initiation_service import create_phone_call
from models.prospect import ProspectIn
import logging
from zoneinfo import ZoneInfo  # Use zoneinfo instead of pytz

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define Australian timezone
AUS_TIMEZONE = ZoneInfo("Australia/Sydney")
# AUS_TIMEZONE = ZoneInfo("Asia/Kolkata")


def get_scheduled_prospects():
    """Fetch prospects that are scheduled for calls today"""
    try:
        collection = get_prospects_collection()
        
        # Get current date in YYYY-MM-DD format using Australian timezone
        current_date = datetime.now(AUS_TIMEZONE).strftime("%Y-%m-%d")
        print("current date in Australia timezone for schedule_calls cron job", current_date)
        
        # Query to find prospects scheduled for today
        query = {
            "scheduledCallDate": {"$regex": f"^{current_date}"},
            "status": "new"  # Only get prospects that haven't been called yet
        }

        prospects = list(collection.find(query))
        logger.info(f"Found {len(prospects)} prospects scheduled for calls today (Australia time)")
        return prospects

    except Exception as e:
        logger.error(f"Error fetching scheduled prospects: {str(e)}")
        raise

def is_within_call_hours():
    """Check if current time is within allowed call hours (10 AM to 7 PM) in Australian timezone"""
    current_time = datetime.now(AUS_TIMEZONE)
    print("current_time",current_time)
    return 10 <= current_time.hour < 19  # 10 AM to 7 PM Australia time

def process_scheduled_calls():
    """Main function to process scheduled calls"""
    try:
        # Check if current time is within allowed call hours in Australian timezone
        if not is_within_call_hours():
            logger.info("Current time in Australia is outside of allowed call hours (10 AM to 7 PM). Skipping calls.")
            return

        # Get prospects scheduled for today
        prospects = get_scheduled_prospects()

        print("prospects",prospects)
        
        if not prospects:
            logger.info("No prospects found scheduled for calls today (Australia time)")
            return

        # Get current time in HH:MM format using Australian timezone
        current_time = datetime.now(AUS_TIMEZONE).strftime("%H:%M")
        logger.info(f"Current time in Australia: {current_time}")
        
        # Filter prospects by scheduled call time
        prospects_to_call = []
        for prospect in prospects:
            scheduled_time = prospect.get("scheduledCallTime", "")
            print("scheduled_time",scheduled_time)
            print("current_time",current_time)
            # If scheduledCallTime matches current time or is empty (backward compatibility)
            if not scheduled_time or scheduled_time == current_time:
                prospects_to_call.append(prospect)
        
        if not prospects_to_call:
            logger.info(f"No prospects found with scheduled call time matching current Australia time ({current_time})")
            return
            
        logger.info(f"Found {len(prospects_to_call)} prospects with matching scheduled call time")

        # Convert MongoDB documents to ProspectIn objects
        prospect_objects = [
            ProspectIn(
                name=prospect["name"],
                phoneNumber=prospect["phoneNumber"],
                businessName=prospect["businessName"],
                scheduledCallDate=datetime.fromisoformat(prospect["scheduledCallDate"].replace("Z", "+00:00")),
                ownerName=prospect.get("ownerName", ""),  # Include the owner name
                campaignId=prospect.get("campaignId", ""),
                scheduledCallTime=prospect.get("scheduledCallTime", "")
            ) for prospect in prospects_to_call
        ]

        # Initiate calls
        logger.info(f"@@@@ --Scheduled Calls------  Initiating scheduled calls for {len(prospect_objects)} prospects")
        create_phone_call(prospect_objects)

    except Exception as e:
        logger.error(f"Error in process_scheduled_calls: {str(e)}")
        raise 