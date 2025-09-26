# routes/stats_route.py

from fastapi import APIRouter, HTTPException, Request
from services.stats_service import (
    get_prospects_summary,
    get_total_calls_made,
    get_connected_calls,
    get_appointments_booked,
    get_number_of_ebooks_sent,
    get_call_back_schedule,
    get_monthly_stats,
    get_calendar_events,
    get_average_call_duration,
    get_matrix_details
)
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/total_calls")
def total_calls(userId: str):
    """Endpoint to get the total number of calls made."""
    try:
        total = get_total_calls_made(userId)
        logger.info(f"Successfully retrieved total calls: {total}")
        return {"total_calls": total}
    except Exception as e:
        logger.error(f"Error getting total calls: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting total calls: {str(e)}")

@router.get("/total_connected_calls")
def connected_calls(userId: str):
    """Endpoint to get the total number of connected calls."""
    try:
        total_connected_calls = get_connected_calls(userId)

        logger.info(f"Successfully retrieved total connected calls: {total_connected_calls}")
        return {"total_connected_calls": total_connected_calls}
    except Exception as e:
        logger.error(f"Error getting total connected calls: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting total connected calls: {str(e)}")

@router.get("/appointments_booked")
def appointments_booked(userId: str):
    """Endpoint to get the total number of appointments booked."""
    try:
        total_appointments = get_appointments_booked(userId)
        logger.info(f"Successfully retrieved total appointments booked: {total_appointments}")
        return {"total_appointments_booked": total_appointments}
    except Exception as e:
        logger.error(f"Error getting total appointments booked: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting total appointments booked: {str(e)}")

@router.get("/total_ebook_sent")
def ebook_sent(userId: str):
    """Endpoint to get the total number of ebook sent."""
    try:
        total_ebook_sent = get_number_of_ebooks_sent(userId)
        logger.info(f"Successfully retrieved total ebooks sent: {total_ebook_sent}")
        return {"total_ebook_sent": total_ebook_sent}
    except Exception as e:
        logger.error(f"Error getting total ebooks sent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting total ebooks sent: {str(e)}")

@router.get("/total_call_backs")
def call_backs(userId: str):
    """Endpoint to get the total number of call backs."""
    try:
        total_call_backs = get_call_back_schedule(userId)
        logger.info(f"Successfully retrieved total call backs: {total_call_backs}")
        return {"total_call_backs": total_call_backs}
    except Exception as e:
        logger.error(f"Error getting total call backs: {str(e)}") 
        raise HTTPException(status_code=500, detail=f"Error getting total call backs: {str(e)}")
    
@router.get("/average_call_duration")
def average_call_duration(userId: str):
    """Endpoint to get the average call duration."""
    try:
        average_call_duration = get_average_call_duration(userId)
        return {"average_call_duration": average_call_duration}
    except Exception as e:
        logger.error(f"Error getting average call duration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting average call duration: {str(e)}")
    
@router.get("/matrix_details")
def matrix_details(id: str, userName: str):
    """Endpoint to get the matrix details."""
    try:
        matrix_details = get_matrix_details(id, userName)
        return {"matrix_details": matrix_details}
    except Exception as e:
        logger.error(f"Error getting matrix details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting matrix details: {str(e)}")

@router.get("/prospects_summary")
def prospects_summary(userId: str):
    """Endpoint to get a summary of prospects with phone number, name, and status."""
    try:
        summary = get_prospects_summary(userId)
        return {"prospects_summary": summary}
    except Exception as e:
        logger.error(f"Error getting prospects summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting prospects summary: {str(e)}")

@router.get("/calendar_events")
def calendar_events(month: int = None, year: int = None, owner_name: str = None, user_role: str = None):
    """Endpoint to get calendar events for all prospects with appointments in a single query.
    
    Query parameters:
        month (int, optional): Month number (1-12) to filter events by
        year (int, optional): Year to filter events by
        owner_name (str, optional): Filter events by owner name
        user_role (str, optional): Filter events by user role (e.g., super_admin)
    """
    try:
        # Validate month and year if provided
        if (month is not None and year is None) or (month is None and year is not None):
            raise HTTPException(
                status_code=400, 
                detail="Both month and year must be provided together if filtering by date"
            )
        
        if month is not None and (month < 1 or month > 12):
            raise HTTPException(status_code=400, detail="Month must be between 1 and 12")
        
        events = get_calendar_events(month, year, owner_name, user_role)
        logger.info(f"Successfully retrieved calendar events: {len(events)} events found")
        logger.info(f"Calendar events: {events}")
        return {"calendar_events": events}
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        logger.error(f"Error getting calendar events: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting calendar events: {str(e)}")

@router.post("/monthly_stats")
async def get_stats_by_month(request: Request):
    """
    Get statistics for a specific month and year
    
    Request body:
    {
        "month": int (1-12),
        "year": int (e.g., 2025)
    }
    """
    try:
        data = await request.json()
        
        # Validate required fields
        if "month" not in data or "year" not in data:
            raise HTTPException(
                status_code=400,
                detail="Both month and year are required"
            )
            
        month = int(data["month"])
        year = int(data["year"])
        
        # Validate month range
        if not (1 <= month <= 12):
            raise HTTPException(
                status_code=400,
                detail="Month must be between 1 and 12"
            )
            
        # Validate year range (basic validation)
        current_year = datetime.now().year
        if not (2020 <= year <= current_year + 5):
            raise HTTPException(
                status_code=400,
                detail=f"Year must be between 2020 and {current_year + 5}"
            )
            
        result = get_monthly_stats(month, year)
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid month or year format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error getting monthly stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting monthly stats: {str(e)}"
        )