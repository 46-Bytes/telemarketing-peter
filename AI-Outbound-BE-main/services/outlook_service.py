import requests
import json
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Body
import os
from dotenv import load_dotenv
from config.configuration import get_configuration
import httpx
import asyncio
from models.token_model import TokenStore
from config.database import get_users_collection
from bson import ObjectId
import logging
from services.microsoft_service import (
    get_microsoft_data,
    refresh_microsoft_token as ms_refresh_token,
    check_token_status as ms_check_token_status,
    call_graph_api_for_user,
    create_calendar_event
)
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Remove the global token and headers
GRAPH_URL = os.getenv("GRAPH_URL")
token = get_configuration()
token_store = TokenStore()

async def refresh_microsoft_token(user_id, refresh_token=None):
    """
    Refresh Microsoft token using the refresh token if available
    
    Args:
        user_id (str): User ID
        refresh_token (str, optional): Microsoft refresh token
        
    Returns:
        dict: New token information or None if refresh failed
    """
    try:
        # Use the microsoft_service implementation
        result = ms_refresh_token(user_id)
        
        if result and result.get("valid"):
            logger.info(f"Token refreshed successfully for user {user_id}")
            # Convert to format expected by existing code
            return {
                "access_token": result.get("access_token", ""),
                "refresh_token": result.get("refresh_token", ""),
                "expires_in": result.get("expiresIn", 3600)
            }
        else:
            logger.error(f"Failed to refresh token for user {user_id}")
            return None
    except Exception as e:
        logger.error(f"Error refreshing Microsoft token: {str(e)}")
        return None

def get_user_token(user_id):
    """
    Get Microsoft token for a specific user
    
    Args:
        user_id (str): User ID
        
    Returns:
        tuple: (access_token, refresh_token, needs_refresh)
    """
    try:
        # Get Microsoft data using microsoft_service
        microsoft_data = get_microsoft_data(user_id)
        
        if not microsoft_data:
            logger.error(f"User not found or no Microsoft data: {user_id}")
            return None, None, False
            
        access_token = microsoft_data.get("access_token")
        refresh_token = microsoft_data.get("refresh_token")
        token_expiry = microsoft_data.get("token_expiry")
        
        # Check if token is expired or about to expire (within 5 minutes)
        needs_refresh = False
        if token_expiry:
            expires_at = datetime.fromisoformat(token_expiry)
            if datetime.now() + timedelta(minutes=5) >= expires_at:
                needs_refresh = True
        else:
            # If no expiry info, assume it needs refresh
            needs_refresh = True
                
        return access_token, refresh_token, needs_refresh
    except Exception as e:
        logger.error(f"Error getting user token: {str(e)}")
        return None, None, False

async def get_user_headers(user_id):
    """
    Get authentication headers for Microsoft Graph API for a specific user.
    Handles token refresh if needed.
    
    Args:
        user_id (str): User ID
        
    Returns:
        dict: Headers including authentication token or None if failed
    """
    access_token, refresh_token, needs_refresh = get_user_token(user_id)
    
    # If token needs refresh, refresh it
    if needs_refresh:
        result = ms_refresh_token(user_id)
        if result and result.get("valid"):
            access_token = result.get("access_token", access_token)
    
    if not access_token:
        logger.error(f"No valid Microsoft token for user {user_id}")
        return None
        
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

async def check_timeslot_availability(user_id, start_time, duration_minutes=60):
    """
    Check if a timeslot is available in Outlook calendar.
    Args:
        user_id (str): User ID
        start_time (str): ISO format, e.g., "2025-04-10T14:00:00"
        duration_minutes (int): Length of the appointment in minutes
    Returns:
        bool: True if available, False if busy
    """
    try:
        # Convert start_time to IST
        start_dt = datetime.fromisoformat(start_time)
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        start_time_ist = start_dt.strftime("%Y-%m-%dT%H:%M:%S")
        end_time_ist = end_dt.strftime("%Y-%m-%dT%H:%M:%S")

        # Get user email from database
        users_collection = get_users_collection()
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        user_email = user.get("microsoft_email") or user.get("email")

        # Payload for getSchedule endpoint
        payload = {
            "schedules": [user_email],  # Check user's calendar
            "startTime": {"dateTime": start_time_ist, "timeZone": "Australia/Sydney"},
            "endTime": {"dateTime": end_time_ist, "timeZone": "Australia/Sydney"},
            "availabilityViewInterval": duration_minutes
        }

        # Call Microsoft Graph API using microsoft_service
        try:
            schedule_info = call_graph_api_for_user(
                user_id, 
                "me/calendar/getSchedule", 
                "POST", 
                payload
            )
            
            if schedule_info and "value" in schedule_info:
                availability_view = schedule_info["value"][0]["availabilityView"]
                return "0" in availability_view  # True if any slot is free
            else:
                logger.error(f"Invalid schedule info response: {schedule_info}")
                return False
        except HTTPException as e:
            if e.status_code == 401:
                # Token expired and couldn't be refreshed
                logger.error(f"Token expired for user {user_id} and couldn't be refreshed")
                return False
            raise
    except Exception as e:
        logger.error(f"Error checking availability: {e}")
        return False

async def create_outlook_event(user_id, start_time, duration_minutes=60, subject="AI-Scheduled Meeting"):
    """
    Create an event in Outlook calendar for a specific user.
    
    Args:
        user_id (str): User ID
        start_time (str): ISO format, e.g., "2025-04-10T14:00:00"
        duration_minutes (int): Length of the appointment in minutes
        subject (str): Meeting subject
        
    Returns:
        bool or dict: True if successful, False if failed, or dict with error info
    """
    try:
        # Convert start_time to IST
        start_dt = datetime.fromisoformat(start_time)
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        start_time_ist = start_dt.strftime("%Y-%m-%dT%H:%M:%S")
        end_time_ist = end_dt.strftime("%Y-%m-%dT%H:%M:%S")

        event_payload = {
            "subject": subject,
            "start": {"dateTime": start_time_ist, "timeZone": "Australia/Sydney"},
            "end": {"dateTime": end_time_ist, "timeZone": "Australia/Sydney"}
        }

        # Use microsoft_service to create calendar event
        try:
            event_result = create_calendar_event(user_id, event_payload)
            logger.info(f"Event created for user {user_id}: {subject} at {start_time_ist}")
            return {"success": True, "event": event_result}
        except HTTPException as e:
            if e.status_code == 401:
                # Token expired and couldn't be refreshed
                return {
                    "success": False, 
                    "error": "Microsoft token is expired and cannot be automatically refreshed",
                    "needs_reauth": True
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to create event: {e.detail}",
                    "status_code": e.status_code
                }
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        return {"success": False, "error": str(e)}

def check_user_microsoft_integration(user_id):
    """
    Check if a user has Microsoft integration set up
    
    Args:
        user_id (str): User ID to check
        
    Returns:
        bool: True if the user has Microsoft integration, False otherwise
    """
    try:
        # Use microsoft_service to get Microsoft data
        microsoft_data = get_microsoft_data(user_id)
        
        # Check if user has Microsoft token
        has_microsoft = (
            microsoft_data and 
            microsoft_data.get("access_token") is not None
        )
        
        if not has_microsoft:
            logger.error(f"User {user_id} does not have Microsoft integration set up")
            
        return has_microsoft
    except Exception as e:
        logger.error(f"Error checking user Microsoft integration: {str(e)}")
        return False

async def schedule_appointment(date, time, phone_number=None, meeting_type="default", campaign_id=None):
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
    logger.info(f"Scheduling appointment with params: date={date}, time={time}, campaign_id={campaign_id}")
    user_id = None
    # If campaign_id is provided, try to get users from the campaign
    if campaign_id:
        try:
            from services.campaign_service import get_campaign_by_id
            from bson import ObjectId
            
            logger.info(f"Attempting to retrieve users from campaign_id: {campaign_id}")
            # Get the campaign by ID
            campaign = get_campaign_by_id(ObjectId(campaign_id))
            logger.info(f"Campaign data retrieved: {campaign}")
            
            if campaign and campaign.get("users"):
                # The users field contains user IDs, possibly as a comma-separated string
                users_field = campaign.get("users")
                logger.info(f"Users field from campaign: {users_field}")
                user_id=users_field
          
        except Exception as e:
            logger.error(f"Error retrieving campaign users: {e}")
            if not user_id:
                return {"error": f"Error retrieving campaign users: {str(e)}"}
            # If there's an error but user_id is provided, continue with the provided user_id
    
    print("user_id inside schedule_appointment", user_id)
    if not user_id:
        logger.error("No user_id provided and couldn't retrieve from campaign")
        return {"error": "User ID is required to schedule an appointment"}
    
    # Check if the user has Microsoft integration set up
    if not check_user_microsoft_integration(user_id):
        return {"error": "The user does not have Microsoft integration set up"}
    
    # Check token status first using microsoft_service directly
    token_status = ms_check_token_status(user_id)
    if not token_status.get("valid"):
        if token_status.get("isExpired"):
            return {
                "error": "Microsoft token is expired and needs to be refreshed",
                "needs_reauth": True,
                "message": token_status.get("message", "Please reconnect your Microsoft account")
            }
        else:
            return {"error": "Invalid Microsoft token", "details": token_status}
    
    # Construct the start_time in ISO format
    start_time = f"{date}T{time}:00"
    duration_minutes = 60  # Default duration
    
    logger.info(f"Checking availability for timeslot {start_time} with user_id {user_id}")
    
    # Determine appointment type from meeting_type parameter
    appointment_type = None
    if meeting_type == "bookSellingAppointment":
        appointment_type = "selling"
    elif meeting_type == "bookSaleAdvisoryAppointment":
        appointment_type = "advisory"
    
    try:
        result = await connect_microsoft(user_id, start_time, duration_minutes)
        logger.info(f"Microsoft connection result: {result}")
        
        print("result while booking", result)
        
        # Check if we need to reauthenticate
        if isinstance(result, dict) and result.get("needs_reauth"):
            return {
                "error": result.get("error", "Microsoft token needs to be refreshed"),
                "needs_reauth": True,
                "message": "Please reconnect your Microsoft account"
            }
        
        # Check if the event was created successfully and has webLink
        if "event" in result and "webLink" in result["event"]:
            web_link = result["event"]["webLink"]
            
            logger.info(f"Web Link: {web_link}")
            # If phone_number is provided, update the prospect's appointment with the webLink
            if phone_number:
                from services.prospect_service import update_prospect_appointment
                
                appointment_update = update_prospect_appointment(
                    phone_number=phone_number,
                    campaign_id=campaign_id,
                    appointment_interest=True,
                    appointment_date_time=start_time,
                    meeting_link=web_link,
                    appointment_type=appointment_type
                )
                logger.info(f"Prospect appointment update result: {appointment_update}")
                
                # Send appointment confirmation email
                try:
                    from services.appointment_email_service import send_appointment_confirmation_email
                    
                    email_result = send_appointment_confirmation_email(
                        phone_number=phone_number,
                        campaign_id=campaign_id
                    )
                    logger.info(f"Appointment confirmation email result: {email_result}")
                except Exception as e:
                    logger.error(f"Error sending appointment confirmation email: {str(e)}")
            
            return {
                "message": f"Timeslot is available. {meeting_type} created successfully.",
                "meetingLink": web_link,
                "event": result["event"]
            }
        
        return result
    except Exception as e:
        logger.error(f"Error connecting to Microsoft: {e}")
        return {"error": f"Error connecting to Microsoft: {str(e)}"}


async def connect_microsoft(user_id: str, start_time: str, duration_minutes: int):
    """
    Connect to Microsoft Graph API to create a calendar event
    
    Args:
        user_id (str): User ID
        start_time (str): Start time in ISO format
        duration_minutes (int): Duration in minutes
        
    Returns:
        dict: Result of the operation
    """
    try:
        logger.info(f"Connecting to Microsoft for user {user_id} at time {start_time}")
        
        # Parse the start_time if it's a string
        if isinstance(start_time, str):
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        else:
            start_dt = start_time
             
        end_dt = start_dt + timedelta(minutes=duration_minutes)

        # Format times in ISO 8601 format
        start_time_str = start_dt.isoformat()
        end_time_str = end_dt.isoformat()

        # Create event payload
        event = {
            "subject": "AI-Call Meeting",
            "start": {
                "dateTime": start_time_str,
                "timeZone": "Australia/Sydney"
            },
            "end": {
                "dateTime": end_time_str,
                "timeZone": "Australia/Sydney"
            },
            "body": {
                "contentType": "text",
                "content": "This is a meeting created by AI-Call application."
            }
        }

        # Use microsoft_service to create calendar event
        try:
            event_result = create_calendar_event(user_id, event)
            return {"message": "Calendar event created successfully", "event": event_result}
        except HTTPException as e:
            if e.status_code == 401:
                # Token expired and couldn't be refreshed
                return {
                    "error": "Microsoft token is expired and cannot be automatically refreshed",
                    "needs_reauth": True,
                    "status_code": 401
                }
            else:
                return {"error": f"Failed to create event. Status: {e.status_code}", "details": e.detail}

    except Exception as e:
        logger.error(f"Error in connect_microsoft: {str(e)}")
        return {"error": f"Error connecting to Microsoft: {str(e)}"}

async def check_token_status(user_id):
    """
    Check the status of a user's Microsoft token
    
    Args:
        user_id (str): User ID
        
    Returns:
        dict: Token status information
    """
    try:
        # Use microsoft_service to check token status
        status = ms_check_token_status(user_id)
        return status
    except Exception as e:
        logger.error(f"Error checking token status: {str(e)}")
        return {
            "valid": False,
            "error": str(e)
        }

# Create a router for Microsoft-related endpoints
microsoft_router = APIRouter(
    prefix="/api/auth/microsoft",
    tags=["microsoft"],
    responses={404: {"description": "Not found"}},
)

@microsoft_router.get("/token/status/{user_id}")
async def get_token_status(user_id: str):
    """
    Check the status of a user's Microsoft token
    
    Args:
        user_id (str): User ID
        
    Returns:
        dict: Token status information
    """
    try:
        # Validate user_id
        if not user_id:
            return {"valid": False, "error": "User ID is required"}
            
        # Check token status using microsoft_service directly
        status = ms_check_token_status(user_id)
        return status
    except Exception as e:
        logger.error(f"Error checking token status: {str(e)}")
        return {"valid": False, "error": str(e)}

@microsoft_router.post("/token/refresh/{user_id}")
async def refresh_token_endpoint(user_id: str, data: dict = Body(...)):
    """
    Refresh a user's Microsoft token using a new access token from the frontend
    
    Args:
        user_id (str): User ID
        data (dict): Contains the new access token
        
    Returns:
        dict: Result of the refresh operation
    """
    try:
        # Validate request
        if not user_id:
            return {"valid": False, "error": "User ID is required"}
            
        access_token = data.get("accessToken")
        if not access_token:
            return {"valid": False, "error": "Access token is required"}
            
        expires_in = data.get("expiresIn")
        
        # Use microsoft_service to refresh token with the correct parameters
        result = ms_refresh_token(user_id, access_token, expires_in)
        return result
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        return {"valid": False, "error": str(e)}

@microsoft_router.post("/connect/{user_id}")
async def connect_microsoft_account(user_id: str, data: dict = Body(...)):
    """
    Connect a Microsoft account to a user
    
    Args:
        user_id (str): User ID
        data (dict): Contains the Microsoft access token and account info
        
    Returns:
        dict: Result of the connection operation
    """
    try:
        # Validate request
        if not user_id:
            return {"valid": False, "error": "User ID is required"}
            
        access_token = data.get("accessToken")
        account = data.get("account")
        
        if not access_token:
            return {"valid": False, "error": "Access token is required"}
            
        if not account:
            return {"valid": False, "error": "Account information is required"}
        
        # Use microsoft_service to connect account
        from services.microsoft_service import connect_microsoft_account as ms_connect_account
        
        result = ms_connect_account(user_id, access_token, account, data.get("expiresOn"))
        return result
    except Exception as e:
        logger.error(f"Error connecting Microsoft account: {str(e)}")
        return {"valid": False, "error": str(e)}