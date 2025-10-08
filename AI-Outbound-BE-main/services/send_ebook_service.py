import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
import requests
import logging
from pathlib import Path
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()   

def send_ebook_email(email: str, pdf_path: str, name: str = None):
    """
    Send an ebook via email. The pdf_path can be either a URL or a local file path.
    """
    # Set up the server
    smtp_user = os.getenv("SMTP_USER_EMAIL")   
    smtp_password = os.getenv("SMTP_PASSWORD")
    
    logger.info(f"Preparing to send ebook to {email}")  
    logger.info(f"PDF path/URL: {pdf_path}")

    # Create the email
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = email
    msg['Subject'] = "Here’s a copy of the ebook you requested"

    # Determine if path is URL or local file
    is_url = pdf_path.startswith(('http://', 'https://'))
    
    # Extract filename from path
    filename = pdf_path.split('/')[-1].split('\\')[-1]  # Handle both / and \ path separators

    try:
        pdf_content = None
        
        if is_url:
            logger.info(f"Downloading PDF from URL: {pdf_path}")
            
            # Try to download with timeout
            try:
                response = requests.get(pdf_path, timeout=10)  # 10 seconds timeout
                response.raise_for_status()  # Raise an exception for bad status codes
                pdf_content = response.content
                logger.info(f"Successfully downloaded PDF, size: {len(pdf_content)} bytes")
            except requests.exceptions.Timeout:
                logger.error(f"Timeout downloading PDF from URL: {pdf_path}")
                # Try to use local path as fallback if it's a localhost URL
                if "localhost" in pdf_path or "127.0.0.1" in pdf_path:
                    logger.info("URL is localhost, trying to access file directly")
                    
                    # Try multiple path variations
                    possible_paths = []
                    
                    # Extract just the filename from the URL
                    url_filename = pdf_path.split('/')[-1]
                    
                    # Add possible paths to try
                    possible_paths.append(Path("public/ebooks") / url_filename)
                    
                    if "/ebooks/" in pdf_path:
                        path_parts = pdf_path.split("/ebooks/")
                        if len(path_parts) > 1:
                            possible_paths.append(Path("public/ebooks") / path_parts[1])
                    
                    # Try each path
                    for try_path in possible_paths:
                        logger.info(f"Trying path: {try_path}")
                        if try_path.exists():
                            logger.info(f"Found file at: {try_path}")
                            with open(try_path, 'rb') as file:
                                pdf_content = file.read()
                            logger.info(f"Successfully read local PDF as fallback, size: {len(pdf_content)} bytes")
                            break
                    
                    if pdf_content is None:
                        # Try default PDF as last resort
                        logger.warning(f"Local file not found, using default PDF")
                        # default_pdf_url = os.getenv("DEFAULT_PDF_URL")
                        default_pdf_url = os.getenv("DEFAULT_PDF_URL")
                        response = requests.get(default_pdf_url, timeout=10)
                        response.raise_for_status()
                        pdf_content = response.content
                        logger.info(f"Successfully downloaded default PDF, size: {len(pdf_content)} bytes")
                else:
                    raise
        else:
            # Handle different path formats
            possible_paths = []
            
            # Just the filename in public/ebooks
            if '/' in pdf_path or '\\' in pdf_path:
                filename = pdf_path.split('/')[-1].split('\\')[-1]
                possible_paths.append(Path("public/ebooks") / filename)
            
            # Path as provided
            possible_paths.append(Path(pdf_path))
            
            # Handle /ebooks/ paths
            if pdf_path.startswith('/ebooks/'):
                possible_paths.append(Path("public") / pdf_path[1:])  # Remove leading slash and prepend public
                possible_paths.append(Path("public/ebooks") / pdf_path.split('/')[-1])  # Just filename in public/ebooks
            
            # Handle public/ebooks paths
            if pdf_path.startswith('public/ebooks/'):
                possible_paths.append(Path(pdf_path))
                possible_paths.append(Path("public/ebooks") / pdf_path.split('/')[-1])
            
            # Try each path
            for try_path in possible_paths:
                logger.info(f"Trying path: {try_path}")
                if try_path.exists():
                    logger.info(f"Found file at: {try_path}")
                    with open(try_path, 'rb') as file:
                        pdf_content = file.read()
                    logger.info(f"Successfully read local PDF, size: {len(pdf_content)} bytes")
                    break
            
            if pdf_content is None:
                # Try default PDF as last resort
                logger.warning(f"Local file not found in any location, using default PDF")
                default_pdf_url = os.getenv("DEFAULT_PDF_URL")
                response = requests.get(default_pdf_url, timeout=10)
                response.raise_for_status()
                pdf_content = response.content
                logger.info(f"Successfully downloaded default PDF, size: {len(pdf_content)} bytes")
        
        if pdf_content is None:
            # Final fallback to default PDF
            logger.warning("Failed to get PDF content, using default PDF as last resort")
            default_pdf_url = os.getenv("DEFAULT_PDF_URL")
            response = requests.get(default_pdf_url, timeout=10)
            response.raise_for_status()
            pdf_content = response.content
            logger.info(f"Successfully downloaded default PDF, size: {len(pdf_content)} bytes")
            
        # Attach the PDF
        attach = MIMEApplication(pdf_content, _subtype="pdf")
        attach.add_header('Content-Disposition', 'attachment', filename="EBook.pdf")
        msg.attach(attach)
        
        # Add text body
        from datetime import datetime

        first_name = name or "There"
        logo_url = "https://www.benchmarkbusiness.com.au/wp-content/uploads/2024/03/Benchmark-Web-Logo-2024-Black-text.png"  # Replace with your actual logo URL
        current_year = datetime.now().year

        body = f"""
        <html>
        <head>
        <meta charset="UTF-8">
        <title>eBook Delivery</title>
        </head>
        <body style="font-family: Arial, sans-serif; color: #333333; line-height: 1.6; margin: 0; padding: 0; background-color: #f9f9f9;">
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
                <td align="center" style="padding: 40px 20px;">
                    <table width="600" cellpadding="0" cellspacing="0" border="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.05);">
                        <tr>
                            <td style="padding: 20px; text-align: center;">
                                <!-- Logo Placeholder -->
                                <img src="{logo_url}" alt="Benchmark Business Group Logo" style="max-width: 450px;">
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 30px;">
                                <p>Hi <strong>{first_name}</strong>,</p>

                                <p>Please find attached to this email a copy of the ebook you had requested.</p>

                                <p>Should we be of any further assistance, don’t hesitate to contact our friendly team for a confidential chat.</p>

                                <p>Regards,<br><br>
                                <strong>Team Benchmark Business Group</strong></p>

                                <p>
                                    <a href="https://www.benchmarkbusiness.com.au" style="color: #1a73e8; text-decoration: none;">www.benchmarkbusiness.com.au</a><br>
                                    <a href="https://www.benchmarkbusinessadvisory.com.au" style="color: #1a73e8; text-decoration: none;">www.benchmarkbusinessadvisory.com.au</a><br><br>
                                    <strong>Phone:</strong> 1300 366 521
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 20px; text-align: center; font-size: 12px; color: #777777;">
                                © {current_year} Benchmark Business Group. All rights reserved.
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        </body>
        </html>
        """

        msg.attach(MIMEText(body, 'html'))
        
        # Send the email
        logger.info("Connecting to SMTP server...")
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        logger.info("Logging in to SMTP server...")
        server.login(smtp_user, smtp_password)
        text = msg.as_string()
        logger.info("Sending email...")
        server.sendmail(smtp_user, email, text)
        server.quit()
        
        logger.info(f"Email with ebook successfully sent to {email}")
        return "Email sent successfully"
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {str(e)}")
        # Try default PDF as last resort
        try:
            logger.warning("Using default PDF after file not found error")
            default_pdf_url = os.getenv("DEFAULT_PDF_URL")
            response = requests.get(default_pdf_url, timeout=10)
            response.raise_for_status()
            pdf_content = response.content
            
            # Attach the PDF
            attach = MIMEApplication(pdf_content, _subtype="pdf")
            attach.add_header('Content-Disposition', 'attachment', filename="default.pdf")
            msg.attach(attach)
            
            # Add text body
            body = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        <title>eBook Delivery</title>
        </head>
        <body style="font-family: Arial, sans-serif; color: #333333; line-height: 1.6; margin: 0; padding: 0; background-color: #f9f9f9;">
        <table width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
                <td align="center" style="padding: 40px 20px;">
                    <table width="600" cellpadding="0" cellspacing="0" border="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.05);">
                        <tr>
                            <td style="padding: 20px; text-align: center;">
                                <!-- Logo Placeholder -->
                                <img src="{logo_url}" alt="Benchmark Business Group Logo" style="max-width: 450px;">
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 30px;">
                                <p>Dear <strong>{first_name}</strong>,</p>

                                <p>Please find attached to this email a copy of the ebook you had requested.</p>

                                <p>Should we be of any further assistance, don’t hesitate to contact our friendly team for a confidential chat.</p>

                                <p>Regards,<br><br>
                                <strong>Team Benchmark Business Group</strong></p>

                                <p>
                                    <a href="https://www.benchmarkbusiness.com.au" style="color: #1a73e8; text-decoration: none;">www.benchmarkbusiness.com.au</a><br>
                                    <a href="https://www.benchmarkbusinessadvisory.com.au" style="color: #1a73e8; text-decoration: none;">www.benchmarkbusinessadvisory.com.au</a><br><br>
                                    <strong>Phone:</strong> 1300 366 521
                                </p>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 20px; text-align: center; font-size: 12px; color: #777777;">
                                © {current_year} Benchmark Business Group. All rights reserved.
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        </body>
        </html>
        """
            msg.attach(MIMEText(body, 'html'))
            
            # Send the email
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(smtp_user, smtp_password)
            text = msg.as_string()
            server.sendmail(smtp_user, email, text)
            server.quit()
            
            logger.info(f"Email with default PDF sent to {email}")
            return "Email sent with default PDF"
        except Exception as inner_e:
            logger.error(f"Error sending default PDF: {str(inner_e)}")
            raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading PDF: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise


# send_ebook_email("outboundcallagent@gmail.com", os.getenv("DEFAULT_PDF_URL"))