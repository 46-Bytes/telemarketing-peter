import schedule
import time
from jobs.scheduled_calls_scheduler import process_scheduled_calls
from jobs.retry_and_call_back_scheduler import schedule_callbacks
from jobs.auto_retry_scheduler import process_auto_retries
import logging
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_scheduler():
    """Run the unified scheduler to process scheduled calls, callbacks, auto-retries, and newsletters"""
    try:
        # Schedule the job to run every day at 9 AM for scheduled calls
        schedule.every(1).minutes.do(lambda: asyncio.run(process_scheduled_calls()))
        # schedule.every().day.at("09:00").do(process_scheduled_calls)
        
        # Schedule callbacks to run every hour (user-requested callbacks)
        schedule.every(1).minutes.do(lambda: asyncio.run(schedule_callbacks()))
        # schedule.every().hour.do(schedule_callbacks)
        
        # Schedule auto-retries to run every 10 minutes (for not-connected calls)
        schedule.every(1).minutes.do(lambda: asyncio.run(process_auto_retries()))
        # schedule.every(10).minutes.do(process_auto_retries)
        
        # Schedule newsletter to run on the first day of every month at 10 
        # schedule.every(1).minutes.do(send_monthly_newsletter)   # later change to every month
        # schedule.every().month.at("10:00").do(send_monthly_newsletter)
        
        # Keep the script running
        while True:
            schedule.run_pending()
            time.sleep(1)  
            
    except Exception as e:
        logger.error(f"Error in scheduler: {str(e)}")
        raise

if __name__ == "__main__":
    run_scheduler() 