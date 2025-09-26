from fastapi import APIRouter, HTTPException, Request
import httpx
import logging

from services.calendly_service import create_calendly_event
# from services.outlook_service import create_outlook_event, schedule_appointment
from services.benchmark_appointment_service import schedule_appointment

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.get("/calendly")
async def add_to_calendly():
    try:
        response_data = await create_calendly_event()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="Failed to create event")

    return {"message": "Appointment booked successfully", "data": response_data}


@router.post("/outlook/{subject}")
async def book_appointment(subject: str, request: Request):
    """
    Book an appointment with the specified subject.
    subject: Either 'bookSellingAppointment' or 'bookSaleAdvisoryAppointment'
    """
    print(subject,"subject")
    print(request,"request")
    logger.info(f"Received request to book appointment with subject: {subject}")
    data = await request.json()
    logger.info(f"Request data: {data}")
    date = data["args"]["date"]
    time = data["args"]["time"]
    phone_number = data["args"].get("phoneNumber")  # Get phone number if provided
    campaign_id = data["args"].get("campaign_id")  # Get campaign ID if provided
    email = data["args"].get("email")

    print("date", date)
    print("time", time)
    print("phone_number", phone_number)
    print("campaign_id", campaign_id)   
    print("user email", email)
    
    try:
        response_data = await schedule_appointment(
            date=date,
            time=time,
            phone_number=phone_number,
            subject=subject,
            meeting_type=subject,
            campaign_id=campaign_id,
            userEmail=email
        )
        logger.info(f"Response data: {response_data}")
        if(response_data.get("error")):
            logger.error(f"Error in response: {response_data.get('error')}")
            return HTTPException(status_code=400, detail=response_data.get("error"))
        
        return {
            "message":  f"{subject} booked successfully",
            "data": response_data
        }
    except httpx.HTTPStatusError as e:
        logger.exception(f"HTTPStatusError while creating {subject}: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Failed to create {subject}")
    except Exception as e:
        logger.exception(f"Exception while booking appointment: {e}")
        raise HTTPException(status_code=500, detail=f"Error booking appointment: {str(e)}")

