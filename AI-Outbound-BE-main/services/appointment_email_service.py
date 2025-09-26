import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
import logging
from services.prospect_service import get_prospect_details_by_phone_number_and_campaign_id
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def send_appointment_confirmation_email(phone_number: str,campaign_id: str = None):
    """
    Find a prospect by phone number, get their email address, and send an appointment confirmation email
    with the meeting link if available.
    
    Args:
        phone_number (str): The prospect's phone number
        campaign_id (str, optional): The campaign ID to filter prospects
        
    Returns:
        dict: Result of the operation
    """
    try:
        # Get prospect details by phone number
        prospect = get_prospect_details_by_phone_number_and_campaign_id(phone_number,campaign_id)
        
        if not prospect or isinstance(prospect, dict) and "message" in prospect:
            logger.error(f"Prospect not found with phone number: {phone_number}")
            return {"status": "error", "message": f"Prospect not found with phone number: {phone_number}"}
        
        # Check if email exists
        email = prospect.get("email")
        if not email:
            logger.error(f"No email address found for prospect with phone number: {phone_number}")
            return {"status": "error", "message": f"No email address found for prospect with phone number: {phone_number}"}
        
        # Check if appointment details exist
        appointment = prospect.get("appointment", {})
        meeting_link = appointment.get("meetingLink")
        appointment_date_time = appointment.get("appointmentDateTime")
        appointment_type = appointment.get("appointmentType", "consultation")
        
        if not meeting_link:
            logger.error(f"No meeting link found for prospect with phone number: {phone_number}")
            return {"status": "error", "message": f"No meeting link found for prospect with phone number: {phone_number}"}
        
        # Format appointment date/time if available
        formatted_date_time = ""
        if appointment_date_time:
            try:
                # Parse ISO format date time
                dt = datetime.fromisoformat(appointment_date_time.replace('Z', '+00:00'))
                formatted_date_time = dt.strftime("%A, %B %d, %Y at %I:%M %p")
            except Exception as e:
                logger.warning(f"Error formatting appointment date: {str(e)}")
                formatted_date_time = appointment_date_time
        
        # Get prospect name
        prospect_name = prospect.get("name", "Valued Customer")
        
        # Set up email server connection
        smtp_user = os.getenv("SMTP_USER_EMAIL")
        smtp_password = os.getenv("SMTP_PASSWORD")
        
        if not smtp_user or not smtp_password:
            logger.error("SMTP credentials not configured")
            return {"status": "error", "message": "Email service not configured"}
        
        # Create the email message
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = email
        msg['Subject'] = f"Your {appointment_type.capitalize()} Appointment Confirmation"
        
        # Create email body with appointment details
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #4a6fa5;">Appointment Confirmation</h2>
            <p>Dear {prospect_name},</p>
            <p>Thank you for scheduling a {appointment_type} appointment with us.</p>
            
            <div style="background-color: #f7f9fc; border-left: 4px solid #4a6fa5; padding: 15px; margin: 20px 0;">
                <h3 style="margin-top: 0;">Appointment Details:</h3>
                <p><strong>Date & Time:</strong> {formatted_date_time}</p>
                <p><strong>Type:</strong> {appointment_type.capitalize()} Appointment</p>
                <p><strong>Meeting Link:</strong> <a href="{meeting_link}" style="color: #4a6fa5;">Click here to join the meeting</a></p>
            </div>
            
            <p>Please click the meeting link above at the scheduled time to join the appointment.</p>
            <p>If you need to reschedule or have any questions, please contact us.</p>
            <p>We look forward to speaking with you!</p>
            <p>Best regards,<br>The Team</p>
        </body>
        </html>
        """
        
        # Attach HTML body
        msg.attach(MIMEText(body, 'html'))
        
        # Connect to SMTP server and send email
        logger.info(f"Sending appointment confirmation email to {email}")
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(smtp_user, smtp_password)
        text = msg.as_string()
        server.sendmail(smtp_user, email, text)
        server.quit()
        
        logger.info(f"Appointment confirmation email successfully sent to {email}")
        
        # Update prospect record to indicate email was sent
        # Note: You might want to add a field in the database to track this
        
        return {
            "status": "success", 
            "message": f"Appointment confirmation email sent to {email}"
        }
        
    except Exception as e:
        logger.error(f"Error sending appointment confirmation email: {str(e)}")
        return {"status": "error", "message": f"Error sending appointment confirmation email: {str(e)}"}

def send_appointment_email_by_phone(phone_number: str, web_link: str = None,campaign_id: str = None):
    """
    Standalone function to send an appointment confirmation email by phone number.
    Can be called directly with a meeting link if it's not yet stored in the prospect record.
    
    Args:
        phone_number (str): The prospect's phone number
        web_link (str, optional): The meeting link to include in the email (overrides stored link)
        campaign_id (str, optional): The campaign ID to filter prospects
        
    Returns:
        dict: Result of the operation
    """
    try:
        # Get prospect details by phone number
        prospect = get_prospect_details_by_phone_number_and_campaign_id(phone_number,campaign_id)
        
        if not prospect or isinstance(prospect, dict) and "message" in prospect:
            logger.error(f"Prospect not found with phone number: {phone_number}")
            return {"status": "error", "message": f"Prospect not found with phone number: {phone_number}"}
        
        # Check if email exists
        email = prospect.get("email")
        if not email:
            logger.error(f"No email address found for prospect with phone number: {phone_number}")
            return {"status": "error", "message": f"No email address found for prospect with phone number: {phone_number}"}
        
        # Get appointment details
        appointment = prospect.get("appointment", {})
        meeting_link = web_link if web_link else appointment.get("meetingLink")
        appointment_date_time = appointment.get("appointmentDateTime")
        appointment_type = appointment.get("appointmentType", "consultation")
        
        if not meeting_link:
            logger.error(f"No meeting link provided or found for prospect with phone number: {phone_number}")
            return {"status": "error", "message": f"No meeting link provided or found for prospect with phone number: {phone_number}"}
        
        # Format appointment date/time if available
        formatted_date_time = ""
        if appointment_date_time:
            try:
                # Parse ISO format date time
                dt = datetime.fromisoformat(appointment_date_time.replace('Z', '+00:00'))
                formatted_date_time = dt.strftime("%A, %B %d, %Y at %I:%M %p")
            except Exception as e:
                logger.warning(f"Error formatting appointment date: {str(e)}")
                formatted_date_time = appointment_date_time
        
        # Get prospect name
        prospect_name = prospect.get("name", "Valued Customer")
        
        # Set up email server connection
        smtp_user = os.getenv("SMTP_USER_EMAIL")
        smtp_password = os.getenv("SMTP_PASSWORD")
        
        if not smtp_user or not smtp_password:
            logger.error("SMTP credentials not configured")
            return {"status": "error", "message": "Email service not configured"}
        
        # Create the email message
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = email
        msg['Subject'] = f"Your {appointment_type.capitalize()} Appointment Confirmation"
        
        # Create email body with appointment details
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #4a6fa5;">Appointment Confirmation</h2>
            <p>Dear {prospect_name},</p>
            <p>Thank you for scheduling a {appointment_type} appointment with us.</p>
            
            <div style="background-color: #f7f9fc; border-left: 4px solid #4a6fa5; padding: 15px; margin: 20px 0;">
                <h3 style="margin-top: 0;">Appointment Details:</h3>
                <p><strong>Date & Time:</strong> {formatted_date_time}</p>
                <p><strong>Type:</strong> {appointment_type.capitalize()} Appointment</p>
                <p><strong>Meeting Link:</strong> <a href="{meeting_link}" style="color: #4a6fa5;">Click here to join the meeting</a></p>
            </div>
            
            <p>Please click the meeting link above at the scheduled time to join the appointment.</p>
            <p>If you need to reschedule or have any questions, please contact us.</p>
            <p>We look forward to speaking with you!</p>
            <p>Best regards,<br>The Team</p>
        </body>
        </html>
        """
        
        # Attach HTML body
        msg.attach(MIMEText(body, 'html'))
        
        # Connect to SMTP server and send email
        logger.info(f"Sending appointment confirmation email to {email}")
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(smtp_user, smtp_password)
        text = msg.as_string()
        server.sendmail(smtp_user, email, text)
        server.quit()
        
        logger.info(f"Appointment confirmation email successfully sent to {email}")
        
        return {
            "status": "success", 
            "message": f"Appointment confirmation email sent to {email}"
        }
        
    except Exception as e:
        logger.error(f"Error sending appointment confirmation email: {str(e)}")
        return {"status": "error", "message": f"Error sending appointment confirmation email: {str(e)}"} 