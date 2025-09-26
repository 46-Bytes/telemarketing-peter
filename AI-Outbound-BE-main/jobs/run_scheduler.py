import schedule
import time
from jobs.scheduled_calls_scheduler import process_scheduled_calls
from jobs.retry_and_call_back_scheduler import schedule_callbacks
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_scheduler():
    """Run the unified scheduler to process scheduled calls, callbacks, and newsletters"""
    try:
        # Schedule the job to run every day at 9 AM for scheduled calls
        schedule.every(1).minutes.do(process_scheduled_calls)
        # schedule.every().day.at("09:00").do(process_scheduled_calls)
        
        # Schedule callbacks to run every hour
        # schedule.every(1).minutes.do(schedule_callbacks)
        # schedule.every().hour.do(schedule_callbacks)
        
        # Schedule newsletter to run on the first day of every month at 10 
        # schedule.every(1).minutes.do(send_monthly_newsletter)   # later change to every month
        # schedule.every().month.at("10:00").do(send_monthly_newsletter)
        
        logger.info("Scheduler started. Will run:")
        logger.info("- Scheduled calls every day at 9 AM")
        logger.info("- Callbacks every hour")
        logger.info("- Newsletter on the first day of every month at 10 AM")
        
        # Keep the script running
        while True:
            schedule.run_pending()
            time.sleep(1)  
            
    except Exception as e:
        logger.error(f"Error in scheduler: {str(e)}")
        raise

if __name__ == "__main__":
    run_scheduler() 