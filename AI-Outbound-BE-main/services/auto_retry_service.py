"""
Auto Retry Service for handling automatic call retries when prospects don't pick up.

This service handles:
1. Scheduling automatic retries with specific timing rules
2. Tracking retry attempts
3. Sending failure notification emails after 3 failed attempts
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import logging
import os
from dotenv import load_dotenv
from config.database import get_prospects_collection, get_campaign_users_collection
from utils.timezone import get_brisbane_now, get_brisbane_date, get_brisbane_time
from bson import ObjectId
from zoneinfo import ZoneInfo


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


def calculate_next_retry_time(retry_count: int, last_call_time: datetime) -> Dict[str, Optional[str]]:
    """
    Calculate the next retry time based on the retry count and last call time.
    
    Rules:
    - First retry: 1 hour later (only before 5pm same day)
    - Second retry: Next day at 10am
    - Third retry: Same day as second at 3pm
    
    Args:
        retry_count (int): Current retry count (0 = first retry, 1 = second retry, etc.)
        last_call_time (datetime): Timestamp of the last call attempt
        
    Returns:
        dict: Contains 'date' (YYYY-MM-DD) and 'time' (HH:MM) for next retry, or None if no more retries
    """
    try:
        # Convert last_call_time to Brisbane timezone if it's not already
        if last_call_time.tzinfo is None:
            from zoneinfo import ZoneInfo
            last_call_time = last_call_time.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo("Australia/Brisbane"))
        else:
            from zoneinfo import ZoneInfo
            last_call_time = last_call_time.astimezone(ZoneInfo("Australia/Brisbane"))
        logger.info(f"Last call time: {last_call_time}")
        if retry_count == 0:
            # First retry: 1 hour later, but only before 5pm
            next_retry_time = last_call_time + timedelta(hours=1)
            
            # Check if next retry time is before 5pm (17:00) on the same day
            if next_retry_time.hour < 18 and next_retry_time.hour > 8:
                return {
                    "date": next_retry_time.strftime("%Y-%m-%d"),
                    "time": next_retry_time.strftime("%H:%M")
                }
            else:
                # If after 5pm, schedule for next day at 10am
                next_day = last_call_time.date() + timedelta(days=1)
                logger.info(f"Next day: {next_day}")
                return {
                    "date": next_day.strftime("%Y-%m-%d"),
                    "time": "10:00"
                }
        
        elif retry_count == 1:
            # Second retry: Next day at 10am
            next_day = last_call_time.date() + timedelta(days=1)
            logger.info(f"Next day: {next_day}")
            return {
                "date": next_day.strftime("%Y-%m-%d"),
                "time": "10:00"
            }
        
        elif retry_count == 2:
            # Third retry: Same day as second retry at 3pm
            # The last_call_time should be from the 10am call
            same_day = last_call_time.date()
            logger.info(f"Same day: {same_day}")
            return {
                "date": same_day.strftime("%Y-%m-%d"),
                "time": "15:00"  # 3pm
            }
        
        else:
            # No more retries after 3 attempts
            return {
                "date": None,
                "time": None
            }
    
    except Exception as e:
        logger.error(f"Error calculating next retry time: {str(e)}")
        return {
            "date": None,
            "time": None
        }


def schedule_auto_retry(phone_number: str, campaign_id: str, call_status: str, call_timestamp: str):
    """
    Schedule an automatic retry for a prospect who didn't pick up the call.
    
    This function is called from the webhook handler when a call is not connected.
    
    Args:
        phone_number (str): Prospect's phone number
        campaign_id (str): Campaign ID
        call_status (str): Status of the call (e.g., 'no_answer', 'busy', 'voicemail')
        call_timestamp (str): ISO timestamp of the call
    """
    try:
        collection = get_prospects_collection()
        
        # Get the prospect
        prospect = collection.find_one({
            "phoneNumber": phone_number,
            "campaignId": campaign_id
        })
        
        if not prospect:
            logger.error(f"Prospect not found for phone {phone_number} in campaign {campaign_id}")
            return
        
        # Check if prospect should be retried
        # Don't retry if:
        # 1. User explicitly declined callback (isCallBack = False)
        # 2. User has an appointment booked
        # 3. Call was picked up (status = 'picked_up')
        if prospect.get("status") == "picked_up":
            logger.info(f"Skipping auto-retry for {phone_number} - call was picked up")
            return
        
        if prospect.get("isCallBack") is False:
            logger.info(f"Skipping auto-retry for {phone_number} - user declined callback")
            return
        
        appointment = prospect.get("appointment", {})
        if appointment.get("appointmentInterest") is True:
            logger.info(f"Skipping auto-retry for {phone_number} - appointment already booked")
            return
        
        # Get current auto retry count
        auto_retry_count = prospect.get("autoRetryCount", 0)
        
        # Check if we've already done 3 retries
        if auto_retry_count >= 3:
            logger.info(f"Maximum auto-retries reached for {phone_number}")
            # Send failure notification email
            send_retry_failure_email(prospect)
            return
        
        # Parse call timestamp
        try:
            call_time = datetime.fromisoformat(call_timestamp)
            # Convert to Brisbane time to match frontend display
            if call_time.tzinfo is None:
                # If naive, assume UTC
                call_time = call_time.replace(tzinfo=ZoneInfo("UTC"))
            # Convert to Brisbane timezone
            call_time = call_time.astimezone(ZoneInfo("Australia/Brisbane"))
            logger.info(f"Call time: {call_time}")
        except Exception as e:
            logger.error(f"Error parsing call timestamp: {str(e)}")
            call_time = get_brisbane_now()
        
        # Calculate next retry time
        next_retry = calculate_next_retry_time(auto_retry_count, call_time)
        
        if not next_retry["date"] or not next_retry["time"]:
            logger.info(f"No more retries scheduled for {phone_number}")
            return
        
        # Record this attempt
        auto_retry_attempt = {
            "attemptNumber": auto_retry_count + 1,
            "callStatus": call_status,
            "timestamp": call_timestamp,
            "scheduledRetryDate": next_retry["date"],
            "scheduledRetryTime": next_retry["time"]
        }
        
        # Update prospect with retry information
        update_result = collection.update_one(
            {
                "phoneNumber": phone_number,
                "campaignId": campaign_id
            },
            {
                "$set": {
                    "autoRetryScheduledDate": next_retry["date"],
                    "autoRetryScheduledTime": next_retry["time"],
                    "updatedAt": {"$date": get_brisbane_now().isoformat() + "Z"}
                },
                "$inc": {
                    "autoRetryCount": 1
                },
                "$push": {
                    "autoRetryAttempts": auto_retry_attempt
                }
            }
        )
        
        if update_result.modified_count > 0:
            logger.info(f"Scheduled auto-retry {auto_retry_count + 1} for {phone_number} on {next_retry['date']} at {next_retry['time']}")
        else:
            logger.warning(f"Failed to schedule auto-retry for {phone_number}")
    
    except Exception as e:
        logger.error(f"Error scheduling auto-retry for {phone_number}: {str(e)}")


def send_retry_failure_email(prospect: Dict):
    """
    Send an email to broker/admin when a prospect has failed all 3 retry attempts.
    
    Args:
        prospect (dict): Prospect document from database
    """
    try:
        # Get SMTP credentials
        smtp_user = os.getenv("SMTP_USER_EMAIL")
        smtp_password = os.getenv("SMTP_PASSWORD")
        recipient_email = os.getenv("REPORT_RECIPIENT_EMAIL")
        
        if not smtp_user or not smtp_password:
            logger.error("SMTP credentials not configured")
            return
        
        # Get campaign details to include owner/admin email
        campaign_id = prospect.get("campaignId")
        if campaign_id:
            try:
                campaign_collection = get_campaign_users_collection()
                campaign = campaign_collection.find_one({"_id": ObjectId(campaign_id)})
                if campaign:
                    # Get campaign owner/users emails if available
                    # For now, we'll send to the default recipient
                    pass
            except Exception as e:
                logger.warning(f"Could not fetch campaign details: {str(e)}")
        
        # Prepare email content
        phone_number = prospect.get("phoneNumber", "Unknown")
        business_name = prospect.get("businessName", "Unknown Business")
        prospect_name = prospect.get("name", "Unknown Contact")
        campaign_name = prospect.get("campaignName", "Unknown Campaign")
        
        # Get all retry attempts
        retry_attempts = prospect.get("autoRetryAttempts", [])
        
        # Format retry attempts for email
        attempts_html = ""
        for attempt in retry_attempts:
            attempt_num = attempt.get("attemptNumber", "N/A")
            timestamp = attempt.get("timestamp", "N/A")
            status = attempt.get("callStatus", "N/A")
            
            # Format timestamp
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime("%A, %B %d, %Y at %I:%M %p")
            except:
                formatted_time = timestamp
            
            attempts_html += f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">{attempt_num}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{formatted_time}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{status}</td>
            </tr>
            """
        
        # Create email message
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = recipient_email
        msg['Subject'] = f"Call Retry Failed - {business_name} ({campaign_name})"
        
        # Create email body
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #d9534f;">Call Retry Attempts Exhausted</h2>
            <p>This is to inform you that after 3 automatic retry attempts, we were unable to connect with the following prospect:</p>
            
            <div style="background-color: #f7f9fc; border-left: 4px solid #d9534f; padding: 15px; margin: 20px 0;">
                <h3 style="margin-top: 0;">Prospect Details:</h3>
                <p><strong>Name:</strong> {prospect_name}</p>
                <p><strong>Business Name:</strong> {business_name}</p>
                <p><strong>Phone Number:</strong> {phone_number}</p>
                <p><strong>Campaign:</strong> {campaign_name}</p>
            </div>
            
            <h3>Call Attempts:</h3>
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <thead>
                    <tr style="background-color: #f2f2f2;">
                        <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Attempt #</th>
                        <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Date & Time</th>
                        <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Outcome</th>
                    </tr>
                </thead>
                <tbody>
                    {attempts_html}
                </tbody>
            </table>
            
            <p>Please consider reaching out to this prospect through alternative methods or at a different time.</p>
            
            <p style="margin-top: 30px; color: #666; font-size: 12px;">
                This is an automated notification from the AI Telemarketing System.
            </p>
        </body>
        </html>
        """
        
        # Attach HTML body
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        logger.info(f"Sending retry failure notification email for {phone_number} to {recipient_email}")
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(smtp_user, smtp_password)
        text = msg.as_string()
        server.sendmail(smtp_user, recipient_email, text)
        server.quit()
        
        logger.info(f"Retry failure notification email sent successfully for {phone_number}")
        
        # Update prospect to indicate notification was sent
        collection = get_prospects_collection()
        collection.update_one(
            {
                "phoneNumber": prospect.get("phoneNumber"),
                "campaignId": prospect.get("campaignId")
            },
            {
                "$set": {
                    "autoRetryFailureEmailSent": True,
                    "autoRetryFailureEmailSentAt": {"$date": get_brisbane_now().isoformat() + "Z"}
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error sending retry failure email: {str(e)}")


def  get_prospects_for_auto_retry() -> List[Dict]:
    """
    Fetch prospects that are due for automatic retry based on scheduled date/time.
    
    Returns:
        list: List of prospect documents that need to be retried
    """
    try:
        collection = get_prospects_collection()
        
        # Get current Brisbane date and time
        current_date = get_brisbane_date()
        current_time = get_brisbane_time()
        
        logger.debug(f"Checking for auto-retries. Current Brisbane date: {current_date}, time: {current_time}")
        
        # Query to find prospects scheduled for auto-retry
        query = {
            "$and": [
                {"autoRetryCount": {"$gt": 0, "$lt": 3}},  # Has retries scheduled (1-3)
                {"autoRetryScheduledDate": current_date},  # Scheduled for today
                {"status": {"$ne": "picked_up"}},  # Not picked up yet
                # {
                #     "$or": [
                #         {"isCallBack": {"$ne": False}},  # User hasn't declined callback
                #         {"isCallBack": None}  # No callback preference set
                #     ]
                # },
                {
                    "$or": [
                        {"appointment.appointmentInterest": {"$ne": True}},  # No appointment
                        {"appointment.appointmentInterest": None}
                    ]
                }
            ]
        }
        
        candidates = list(collection.find(query))
        
        # Filter by time - only include prospects whose scheduled time exactly matches current time
        prospects = []
        for p in candidates:
            scheduled_time = p.get("autoRetryScheduledTime")
            if scheduled_time and isinstance(scheduled_time, str):
                try:
                    # Normalize time format
                    parts = scheduled_time.split(":")
                    if len(parts) >= 2:
                        if len(parts[0]) == 1:
                            scheduled_time_norm = f"0{parts[0]}:{parts[1]}"
                        else:
                            scheduled_time_norm = scheduled_time
                        
                        # Only include if current time exactly matches scheduled time
                        if current_time == scheduled_time_norm:
                            prospects.append(p)
                        else:
                            logger.debug(f"Auto-retry not due for {p.get('phoneNumber')} - scheduled at {scheduled_time_norm}, current time {current_time}")
                except Exception as e:
                    logger.warning(f"Error parsing scheduled time for prospect {p.get('phoneNumber')}: {str(e)}")
                    # Don't include if we can't parse time
            else:
                # No time specified, don't include it
                logger.debug(f"Skipping prospect {p.get('phoneNumber')} - no autoRetryScheduledTime set")
        
        logger.debug(f"Found {len(prospects)} prospects due for auto-retry")
        return prospects
    
    except Exception as e:
        logger.error(f"Error fetching prospects for auto-retry: {str(e)}")
        return []


def reset_auto_retry_fields_on_success(phone_number: str, campaign_id: str):
    """
    Reset auto-retry fields when a prospect successfully picks up a call.
    
    Args:
        phone_number (str): Prospect's phone number
        campaign_id (str): Campaign ID
    """
    try:
        collection = get_prospects_collection()
        
        update_result = collection.update_one(
            {
                "phoneNumber": phone_number,
                "campaignId": campaign_id
            },
            {
                "$set": {
                    "autoRetryScheduledDate": None,
                    "autoRetryScheduledTime": None,
                    "updatedAt": {"$date": get_brisbane_now().isoformat() + "Z"}
                }
            }
        )
        
        if update_result.modified_count > 0:
            logger.info(f"Reset auto-retry fields for {phone_number} after successful call")
    
    except Exception as e:
        logger.error(f"Error resetting auto-retry fields: {str(e)}")


