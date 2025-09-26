from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
from services.appointment_email_service import send_appointment_confirmation_email, send_appointment_email_by_phone

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

appointment_email_router = APIRouter(
    prefix="/appointment-email",
    tags=["appointment-email"],
    responses={404: {"description": "Not found"}},
)

class AppointmentEmailRequest(BaseModel):
    phone_number: str
    web_link: Optional[str] = None
    campaign_id: Optional[str] = None

@appointment_email_router.post("/send")
async def send_appointment_email(request: AppointmentEmailRequest = Body(...)):
    """
    Send an appointment confirmation email to a prospect by phone number
    """
    try:
        logger.info(f"Received request to send appointment email to prospect with phone: {request.phone_number}")
        
        # If web_link is provided, use the standalone function
        if request.web_link:
            result = send_appointment_email_by_phone(
                phone_number=request.phone_number,
                web_link=request.web_link,
                campaign_id=request.campaign_id
            )
        else:
            # Otherwise use the standard function that gets the link from the prospect record
            result = send_appointment_confirmation_email(
                phone_number=request.phone_number,
                campaign_id=request.campaign_id
            )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("message"))
        
        return result
    except Exception as e:
        logger.error(f"Error sending appointment email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending appointment email: {str(e)}") 