"""
Timezone utility functions for Brisbane, Australia timezone handling.
All functions use Australia/Brisbane timezone consistently across the application.
"""
from datetime import datetime
from zoneinfo import ZoneInfo
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Brisbane timezone constant
BRISBANE_TZ = ZoneInfo("Australia/Brisbane")

def get_brisbane_now():
    """Get current datetime in Brisbane timezone"""
    return datetime.now(BRISBANE_TZ)

def get_brisbane_date():
    """Get current date in YYYY-MM-DD format in Brisbane timezone"""
    return get_brisbane_now().strftime("%Y-%m-%d")

def get_brisbane_time():
    """Get current time in HH:MM format in Brisbane timezone"""
    return get_brisbane_now().strftime("%H:%M")

def get_brisbane_datetime_iso():
    """Get current datetime in ISO format in Brisbane timezone"""
    return get_brisbane_now().isoformat()

def is_within_call_hours():
    """Check if current time is within allowed call hours (10 AM to 7 PM) in Brisbane timezone"""
    current_time = get_brisbane_now()
    logger.info(f"Current Brisbane time: {current_time}")
    logger.info(f"Current hour: {current_time.hour}")
    return 10 <= current_time.hour < 19

def format_brisbane_datetime(dt_string):
    """Convert datetime string to Brisbane timezone and format for display"""
    try:
        if isinstance(dt_string, str):
            # Handle different datetime formats
            if 'T' in dt_string:
                dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(dt_string, '%Y-%m-%d')
            
            # Convert to Brisbane timezone
            brisbane_dt = dt.astimezone(BRISBANE_TZ)
            return brisbane_dt
        return None
    except Exception as e:
        logger.error(f"Error formatting datetime {dt_string}: {str(e)}")
        return None

def get_brisbane_timezone_info():
    """Get detailed timezone information for debugging"""
    now = get_brisbane_now()
    return {
        "brisbane_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "brisbane_date": now.strftime("%Y-%m-%d"),
        "brisbane_time_only": now.strftime("%H:%M"),
        "timezone_name": str(BRISBANE_TZ),
        "utc_offset": now.strftime("%z"),
        "is_dst": now.dst() != None
    }
