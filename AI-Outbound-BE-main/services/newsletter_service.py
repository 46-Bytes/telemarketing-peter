import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
from services.prospect_service import get_prospects_collection
import logging
from datetime import datetime

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_newsletter_email(email: str):
    """Send newsletter email to a subscriber"""
    try:
        # Set up the server
        smtp_user = os.getenv("SMTP_USER_EMAIL")   
        smtp_password = os.getenv("SMTP_PASSWORD")

        # Create the email
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = email
        msg['Subject'] = "Benchmark Business Sales & Valuations Monthly Newsletter"

        # Create HTML body with newsletter content
        html_body = """
        <html>
            <head></head>
            <body style="font-family: Arial, sans-serif; background-color: #f4f4f9; color: #333; padding: 20px;">
                <div style="max-width: 600px; margin: auto; padding: 20px; background-color: #ffffff; border-radius: 10px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);">
                    <h1 style="color: #4CAF50; text-align: center;">Monthly Business Insights</h1>
                    <p style="font-size: 16px;">Dear Valued Subscriber,</p>
                    <p style="font-size: 16px;">Thank you for subscribing to our monthly newsletter. Here are this month's insights and updates:</p>
                    
                    <!-- Add your newsletter content here -->
                    <div style="margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-radius: 5px;">
                        <h2 style="color: #2c3e50;">Market Updates</h2>
                        <p>Latest trends and insights in business sales and valuations...</p>
                    </div>
                    
                    <div style="margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-radius: 5px;">
                        <h2 style="color: #2c3e50;">Success Stories</h2>
                        <p>Recent successful business sales and client testimonials...</p>
                    </div>
                    
                    <p style="font-size: 16px;">Best Regards,<br><span style="color: #4CAF50;">Benchmark Business Sales & Valuations Team</span></p>
                </div>
            </body>
        </html>
        """
        msg.attach(MIMEText(html_body, 'html'))

        # Send the email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        logger.info(f"Newsletter sent successfully to {email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send newsletter to {email}: {str(e)}")
        return False

def get_subscribed_prospects():
    """Fetch prospects who are subscribed to newsletter and haven't received it yet"""
    try:
        collection = get_prospects_collection()
        
        # Query to find prospects who are subscribed and haven't received newsletter
        query = {
            "isNewsletterSent": True,
            "email": {"$exists": True, "$ne": None}  # Ensure email exists and is not null
        }
        
        prospects = list(collection.find(query))
        logger.info(f"Found {len(prospects)} prospects for newsletter")
        return prospects
    except Exception as e:
        logger.error(f"Error fetching subscribed prospects: {str(e)}")
        raise
