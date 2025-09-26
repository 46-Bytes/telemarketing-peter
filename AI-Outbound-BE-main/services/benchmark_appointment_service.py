import os
import httpx
from typing import Optional, Dict, Any
import logging
from datetime import datetime, timedelta
from services.user_service import get_user_by_id
import re
from config.database import get_users_collection as db_get_users_collection
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

BENCHMARK_API_PATH = os.getenv("BENCHMARK_API_PATH")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_benchmark_appointment(
    api_key: str,
    brokeremail: str,
    start: str,
    end: str,
    subject: str,
    description: str,
    email: str
) -> Dict[str, Any]:
    """
    Create an appointment using the Benchmark API.
    Args:
        brokeremail (str): Broker's email address
        start (str): Start datetime in ISO 8601 (broker's local time)
        end (str): End datetime in ISO 8601 (broker's local time)
        subject (str): Appointment subject
        description (str): Appointment description (supports multiline)
    Returns:
        dict: API response, including success or error
    """
    if not BENCHMARK_API_PATH:
        print("[DEBUG] BENCHMARK_API_PATH not set")
        return {"success": False, "error": "Benchmark API key not set in environment."}
    url = f"{BENCHMARK_API_PATH}/createappointment?apikey={api_key}"
    payload = {
        "brokeremail": brokeremail,
        "start": start,
        "end": end,
        "subject": subject,
        "description": description,
        "email": email
    }
    print("[DEBUG] create_benchmark_appointment payload:", payload)
    print("[DEBUG] create_benchmark_appointment url:", url)
    headers = {"Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            print("[DEBUG] create_benchmark_appointment response status:", response.status_code)
            data = response.json()
            print("[DEBUG] create_benchmark_appointment response data:", data)
        except Exception as e:
            print("[DEBUG] create_benchmark_appointment exception:", str(e))
            return {"success": False, "error": f"Request failed: {str(e)}"}
        if response.status_code == 200 and data.get("success"):
            return {"success": True, "appointmentid": data.get("appointmentid")}
        else:
            return {"success": False, "error": data.get("error", "Unknown error")}


async def get_appointment_list(
    api_key: str,
    brokeremail: str,
    start: str,
    end: str
) -> Dict[str, Any]:
    """
    Retrieve appointments for a broker using the Benchmark API.
    Args:
        api_key (str): Benchmark API key
        brokeremail (str): Broker's email address
        start (str): Start datetime in ISO 8601 (broker's local time) - yyyy-MM-ddTHH:mm:ss
        end (str): End datetime in ISO 8601 (broker's local time) - yyyy-MM-ddTHH:mm:ss
    Returns:
        dict: API response with appointment list or error
    """
    if not BENCHMARK_API_PATH:
        print("[DEBUG] BENCHMARK_API_PATH not set")
        return {"success": False, "error": "Benchmark API key not set in environment."}
    
    url = f"{BENCHMARK_API_PATH}/appointmentlist?apikey={api_key}"
    payload = {
        "brokeremail": brokeremail,
        "start": start,
        "end": end
    }
    print("[DEBUG] get_appointment_list payload:", payload)
    print("[DEBUG] get_appointment_list url:", url)
    headers = {"Content-Type": "application/json"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            print("[DEBUG] get_appointment_list response status:", response.status_code)
            data = response.json()
            print("[DEBUG] get_appointment_list response data:", data)
            logger.info(f"[BENCHMARK] Appointment list retrieved successfully for broker: {brokeremail}")
            return {"success": True, "appointments": data}
        except Exception as e:
            print("[DEBUG] get_appointment_list exception:", str(e))
            logger.error(f"[BENCHMARK] Failed to fetch appointment list for broker {brokeremail}: {str(e)}")
            return {"success": False, "error": f"Request failed: {str(e)}"}


async def check_availability(
    api_key: str,
    brokeremail: str,
    start: str,
    end: str
) -> Dict[str, Any]:
    """
    Check if a time slot is available for a broker using the Benchmark API.
    Args:
        api_key (str): Benchmark API key
        brokeremail (str): Broker's email address
        start (str): Start datetime in ISO 8601 (broker's local time) - yyyy-MM-ddTHH:mm:ss
        end (str): End datetime in ISO 8601 (broker's local time) - yyyy-MM-ddTHH:mm:ss
    Returns:
        dict: API response with availability status or error
    """
    if not BENCHMARK_API_PATH:
        print("[DEBUG] BENCHMARK_API_PATH not set")
        return {"success": False, "error": "Benchmark API key not set in environment."}
    
    url = f"{BENCHMARK_API_PATH}/availabilitycheck?apikey={api_key}"
    payload = {
        "brokeremail": brokeremail,
        "start": start,
        "end": end
    }
    print("[DEBUG] check_availability payload:", payload)
    print("[DEBUG] check_availability url:", url)
    headers = {"Content-Type": "application/json"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            print("[DEBUG] check_availability response status:", response.status_code)
            data = response.json()
            print("[DEBUG] check_availability response data:", data)
            logger.info(f"[BENCHMARK] Availability check completed for broker: {brokeremail}, available: {data.get('available', False)}")
            return {"success": True, "available": data.get("available", False)}
        except Exception as e:
            print("[DEBUG] check_availability exception:", str(e))
            logger.error(f"[BENCHMARK] Failed to check availability for broker {brokeremail}: {str(e)}")
            return {"success": False, "error": f"Request failed: {str(e)}"}


async def check_availability_by_campaign(date: str, time: str, campaign_id: str) -> Dict[str, Any]:
    """
    Check availability for a broker by campaign ID, date, and time.
    Args:
        date (str): Date in "YYYY-MM-DD" format
        time (str): Time in "HH:MM" 24-hour format
        campaign_id (str): Campaign ID to find the broker
    Returns:
        dict: API response with availability status or error
    """
    from services.campaign_service import get_campaign_by_id
    from bson import ObjectId

    # Validate date and time
    if not date or not is_valid_date(date):
        return {"success": False, "error": "Invalid or missing date. Expected format: YYYY-MM-DD"}
    if not time or not is_valid_time(time):
        return {"success": False, "error": "Invalid or missing time. Expected format: HH:MM (24-hour)"}
    if not campaign_id:
        return {"success": False, "error": "Missing campaign_id."}

    # Get campaign and user
    try:
        campaign = get_campaign_by_id(ObjectId(campaign_id))
        if not campaign or not campaign.get("users"):
            return {"success": False, "error": "No users found in campaign."}
        user_id = campaign.get("users")
    except Exception as e:
        return {"success": False, "error": f"Error retrieving campaign: {str(e)}"}

    user = get_user_by_id(user_id)
    if not user or "email" not in user:
        return {"success": False, "error": "User email not found for campaign."}
    user_email = user["email"]
    if not is_valid_email(user_email):
        return {"success": False, "error": "Invalid user email format."}
    api_key = user.get("api_key")
    if not api_key:
        return {"success": False, "error": "The user does not have api key"}

    # Construct start and end datetimes
    start_time = f"{date}T{time}:00"
    try:
        start_dt = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S")
        end_dt = start_dt + timedelta(hours=1)
        end_time = end_dt.strftime("%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return {"success": False, "error": "Invalid start or end datetime format."}

    # Call check_availability
    return await check_availability(
        api_key=api_key,
        brokeremail=user_email,
        start=start_time,
        end=end_time
    )


def is_valid_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def is_valid_time(time_str):
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False

def is_valid_email(email):
    # Improved regex for email validation
    return re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email) is not None

async def schedule_appointment(date, time, phone_number=None, subject: str = None, meeting_type="default", campaign_id=None, userEmail: str = None):
    """
    Check availability and schedule if free.
    Args:
        user_id (str): User ID for the Microsoft account to use
        date (str): Date in "YYYY-MM-DD" format
        time (str): Time in "HH:MM" 24-hour format
        phone_number (str, optional): The prospect's phone number
        meeting_type (str): Type of appointment ("selling" or "advisory")
        campaign_id (str, optional): Campaign ID
    Returns:
        dict: Contains meeting info including webLink if successful
    """
    logger.info(f"[APPOINTMENT] Starting appointment scheduling - Date: {date}, Time: {time}, Campaign ID: {campaign_id}, Meeting Type: {meeting_type}")
    user_id = None

     # Determine appointment type from meeting_type parameter
    appointment_type = None
    if meeting_type == "bookSellingAppointment":
        appointment_type = "selling"
    elif meeting_type == "bookSaleAdvisoryAppointment":
        appointment_type = "advisory"
        
    # If campaign_id is provided, try to get users from the campaign
    if campaign_id:
        try:
            from services.campaign_service import get_campaign_by_id
            from bson import ObjectId
            
            logger.info(f"[CAMPAIGN] Retrieving users from campaign ID: {campaign_id}")
            # Get the campaign by ID
            campaign = get_campaign_by_id(ObjectId(campaign_id))
            logger.info(f"[CAMPAIGN] Campaign data retrieved successfully - Campaign ID: {campaign_id}")
            
            if campaign and campaign.get("users"):
                # The users field contains user IDs, possibly as a comma-separated string
                users_field = campaign.get("users")
                logger.info(f"[CAMPAIGN] Users found in campaign - Campaign ID: {campaign_id}, Users: {users_field}")
                user_id=users_field
          
        except Exception as e:
            logger.error(f"[CAMPAIGN] Failed to retrieve campaign users for campaign ID {campaign_id}: {str(e)}")
            if not user_id:
                return {"error": f"Error retrieving campaign users: {str(e)}"}
            # If there's an error but user_id is provided, continue with the provided user_id
    
    print("[DEBUG] user_id after campaign lookup:", user_id)
    if not user_id:
        logger.error("[APPOINTMENT] No user_id available - cannot proceed with appointment scheduling")
        return {"error": "User ID is required to schedule an appointment"}
    # Input validation
    if not date or not is_valid_date(date):
        return {"error": "Invalid or missing date. Expected format: YYYY-MM-DD"}
    if not time or not is_valid_time(time):
        return {"error": "Invalid or missing time. Expected format: HH:MM (24-hour)"}
    user = get_user_by_id(user_id)
    if not user or "email" not in user:
        return {"error": "User email not found."}
    user_email = user["email"]
    if not is_valid_email(user_email):
        return {"error": "Invalid user email format."}

    # Construct start_time and end_time
    start_time = f"{date}T{time}:00"
    duration_minutes = 60  # Default duration
    try:
        start_dt = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S")
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        end_time = end_dt.strftime("%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return {"error": "Invalid start or end datetime format."}

    if end_dt <= start_dt:
        return {"error": "End time must be after start time."}

    # Now call with both start and end
    # Get API key from user
    api_key = user.get("api_key")
    if not api_key:
        return {"error": "The user does not have api key"}

    # Check availability before booking
    availability = await check_availability(
        api_key=api_key,
        brokeremail=user_email,
        start=start_time,
        end=end_time
    )
    print("[DEBUG] availability result:", availability)
    if not availability.get("success"):
        return {"error": availability.get("error", "Failed to check availability")}
    if not availability.get("available"):
        return {"error": "The selected time slot is not available. Please choose another time."}

    user_name = user.get("name", user_email)
    subjectValue = f"Appointment with {user_name} on {date} at {time}"
    from services.prospect_service import get_prospect_details_by_phone_number_and_campaign_id
    # Fetch prospect details
    prospect = get_prospect_details_by_phone_number_and_campaign_id(phone_number, campaign_id)
    prospect_name = prospect.get("name", "N/A")
    prospect_business_name = prospect.get("businessName", "N/A")
    prospect_phone_number = prospect.get("phoneNumber", "N/A")
    prospect_campaign_name = prospect.get("campaignName", "N/A")
    prospect_email = prospect.get("email")

    # Construct appointment description
    description = (
        f"This is a {meeting_type} meeting scheduled for {user_name} "
        f"({user_email}) on {date} at {time}.\n"
        f"Prospect Name: {prospect_name}\n"
        f"{f'Prospect Email: {prospect_email}' if prospect_email else f'User Email: {userEmail}' if userEmail else ''}\n"
        f"Prospect Phone Number: {prospect_phone_number}\n"
        f"Prospect Campaign Name: {prospect_campaign_name}\n"
        f"Prospect Business Name: {prospect_business_name}"
    )

    logger.info(f"[APPOINTMENT] Description: {description}")

    # Create the appointment
    result = await create_benchmark_appointment(
        api_key=api_key,
        brokeremail=user_email,
        start=start_time,
        end=end_time,
        subject=subject or subjectValue,
        description=description,
        email=userEmail
    )

    print("[DEBUG] create_benchmark_appointment result:", result)

    # Get super admin users
    users_collection = db_get_users_collection()
    super_admins = list(users_collection.find({"role": "super_admin"}))

    # Set up SMTP credentials
    smtp_user = os.getenv("SMTP_USER_EMAIL")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not smtp_user or not smtp_password:
        logger.error("SMTP credentials not configured")
        return {"status": "error", "message": "Email service not configured"}

    # Prepare the email content
    for admin in super_admins:
        admin_email = admin.get("email")
        admin_name = admin.get("name", "Team")

        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = admin_email
        msg['Subject'] = f"{user_name} {appointment_type.capitalize()} Appointment Confirmation"

        # Construct the email body
        body = f"""
            <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #ffffff; color: #333;">

        <!-- Logo Section -->
        <div style="text-align: center; margin-bottom: 30px;">
            <img src="https://www.benchmarkbusiness.com.au/wp-content/uploads/2024/03/Benchmark-Web-Logo-2024-Black-text.png" 
                alt="Benchmark Business Logo" style="max-width: 250px; height: auto;">
        </div>

        <!-- Header -->
        <h2 style="color: #4a6fa5;">Appointment Confirmation</h2>

        <!-- Intro -->
        <p>Dear {admin_name},</p>
        <p>
            A new <strong>{appointment_type}</strong> appointment has been scheduled.
        </p>

        <!-- Appointment Details Box -->
        <div style="background-color: #f7f9fc; border-left: 4px solid #4a6fa5; padding: 15px 20px; margin: 25px 0;">
            <h3 style="margin-top: 0; color: #4a6fa5;">Appointment Details</h3>
            
            <p><strong>Date & Time:</strong> {start_time[:10]} {start_time[11:16]} to {end_time[:10]} {end_time[11:16]}</p>
            <p><strong>Scheduled By:</strong> {user_name} ({user_email})</p>
            <p><strong>Prospect Name:</strong> {prospect_name}</p>
            <p><strong>Prospect Email:</strong> {prospect_email or userEmail}</p>
            <p><strong>Prospect Phone:</strong> {prospect_phone_number}</p>
            <p><strong>Campaign Name:</strong> {prospect_campaign_name}</p>
            <p><strong>Business Name:</strong> {prospect_business_name}</p>
        </div>

        <!-- Footer -->
        <p>Please attend or follow up as needed.</p>

        <p>Regards,<br>{user_name}</p>

        </body>
        </html>
        """

        msg.attach(MIMEText(body, 'html'))

        # Send email
        try:
            logger.info(f"Sending appointment confirmation email to {admin_email}")
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, admin_email, msg.as_string())
            server.quit()
            logger.info(f"Appointment confirmation email successfully sent to {admin_email}")
        except Exception as e:
            logger.error(f"Failed to send email to {admin_email}: {e}")

 
    if phone_number:
        from services.prospect_service import update_prospect_appointment

        appointment_update = update_prospect_appointment(
            phone_number=phone_number,
            campaign_id=campaign_id,
            appointment_interest=True,
            appointment_date_time=start_time,
            meeting_link="",  
            appointment_type=appointment_type
        )
        print("[DEBUG] appointment_update:", appointment_update)
        logger.info(f"[PROSPECT] Prospect appointment updated successfully - Phone: {phone_number}, Campaign ID: {campaign_id}")

        # Send appointment confirmation email
        try:
            from services.appointment_email_service import send_appointment_confirmation_email

            # email_result = send_appointment_confirmation_email(
            #     phone_number=phone_number,
            #     campaign_id=campaign_id
            # )
            print("[DEBUG] email_result:")
            # logger.info(f"[EMAIL] Appointment confirmation email sent successfully - Phone: {phone_number}, Campaign ID: {campaign_id}")
        except Exception as e:
            logger.error(f"[EMAIL] Failed to send appointment confirmation email - Phone: {phone_number}, Campaign ID: {campaign_id}, Error: {str(e)}")

        # Prepare response
        response = {
            "message": f"Timeslot is available. {meeting_type} created successfully."
        }
        # If result contains a meeting link or event, add them
        if isinstance(result, dict):
            if "appointmentid" in result:
                response["appointmentId"] = result["appointmentid"]
            if "meetingLink" in result:
                response["meetingLink"] = result["meetingLink"]
            if "event" in result:
                response["event"] = result["event"]
        return response

    return result
