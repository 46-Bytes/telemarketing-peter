import httpx
from dotenv import load_dotenv
import os

load_dotenv()

async def create_calendly_event():
    calendly_api_url = "https://api.calendly.com/scheduled_events"
    headers = {
        "Authorization": f"Bearer {os.getenv('CALENDLY_API_KEY')}",
        "Content-Type": "application/json"
    }
    data = {
        "event": {
            "name": "New Appointment",
            "start_time": "2025-04-10T10:00:00Z",
            "end_time": "2025-04-10T11:00:00Z"
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(calendly_api_url, headers=headers, json=data)
        print(response)
        response.raise_for_status() 
    return response.json()