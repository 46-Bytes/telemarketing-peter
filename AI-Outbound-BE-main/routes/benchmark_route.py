from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
from services.benchmark_appointment_service import (
    get_appointment_list,
    check_availability,
)
from services.user_service import get_user_by_id

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

benchmark_router = APIRouter(
    prefix="/benchmark",
    tags=["benchmark"],
    responses={404: {"description": "Not found"}},
)

class AppointmentListRequest(BaseModel):
    user_id: str
    start: str  # ISO 8601 format: yyyy-MM-ddTHH:mm:ss
    end: str    # ISO 8601 format: yyyy-MM-ddTHH:mm:ss

class AvailabilityCheckRequest(BaseModel):
    user_id: str
    start: str  # ISO 8601 format: yyyy-MM-ddTHH:mm:ss
    end: str    # ISO 8601 format: yyyy-MM-ddTHH:mm:ss

class CreateAppointmentRequest(BaseModel):
    user_id: str
    start: str  # ISO 8601 format: yyyy-MM-ddTHH:mm:ss
    end: str    # ISO 8601 format: yyyy-MM-ddTHH:mm:ss
    subject: str
    description: str

@benchmark_router.post("/appointmentlist")
async def get_appointments(request: AppointmentListRequest = Body(...)):
    """
    Retrieve appointments for a broker
    """
    try:
        logger.info(f"Received request to get appointments for user_id: {request.user_id}")
        
        # Get user details
        user = get_user_by_id(request.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not user.get("email"):
            raise HTTPException(status_code=400, detail="User email not found")
        
        api_key = user.get("api_key")
        if not api_key:
            raise HTTPException(status_code=400, detail="User does not have API key")
        
        # Call the service function
        result = await get_appointment_list(
            api_key=api_key,
            brokeremail=user["email"],
            start=request.start,
            end=request.end
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to fetch appointments"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting appointments: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting appointments: {str(e)}")

@benchmark_router.post("/availabilitycheck")
async def check_availability_endpoint(request: AvailabilityCheckRequest = Body(...)):
    """
    Check if a time slot is available for a broker
    """
    try:
        logger.info(f"Received request to check availability for user_id: {request.user_id}")
        
        # Get user details
        user = get_user_by_id(request.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not user.get("email"):
            raise HTTPException(status_code=400, detail="User email not found")
        
        api_key = user.get("api_key")
        if not api_key:
            raise HTTPException(status_code=400, detail="User does not have API key")
        
        # Call the service function
        result = await check_availability(
            api_key=api_key,
            brokeremail=user["email"],
            start=request.start,
            end=request.end
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to check availability"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking availability: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error checking availability: {str(e)}")
