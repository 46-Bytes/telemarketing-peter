# API routes

from datetime import datetime
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request
from typing import List
from models.prospect import ProspectIn
from services.call_initiation_service import create_phone_call
from services.prospect_service import (
    upload_prospects_service,
    get_prospects_by_campaign,
    get_prospect_by_phone_number
)
from config.database import get_campaign_users_collection
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
router = APIRouter()

def format_phone_number(phone_number: str) -> str:
    """
    Format phone number by adding '+' prefix and Australian country code if needed.
    Removes any spaces, dashes, or parentheses before adding '+'.
    For Australian numbers, adds +61 country code based on digit count.
    
    Args:
        phone_number (str): Raw phone number from CSV
        
    Returns:
        str: Formatted phone number with '+' prefix and country code
    """
    if not phone_number:
        return phone_number
    
    # Remove any spaces, dashes, parentheses, and other non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone_number.strip())
    
    # If it doesn't start with +, add it
    if not cleaned.startswith('+'):
        cleaned = '+' + cleaned
    
    # Handle Australian phone number formatting
    # Count only digits (excluding the +)
    digits_only = cleaned[1:] if cleaned.startswith('+') else cleaned
    
    # If number starts with 0, replace with +61
    if digits_only.startswith('0'):
        cleaned = '+61' + digits_only[1:]  # Remove the leading 0 and add +61
    # If we have exactly 9 digits, add +61
    elif len(digits_only) == 9:
        cleaned = '+61' + digits_only
    # If we have exactly 10 digits and doesn't start with 61, add +6
    elif len(digits_only) == 10 and not digits_only.startswith('61'):
        cleaned = '+6' + digits_only

    return cleaned

@router.get("/demo")
async def demo():
    return {"message": "Hello World"}

@router.post("/create-prospects-and-call-initiation")
async def upload_prospects(request: Request):
    try:
        data = await request.json()
        print("Received data:", data)
        
        # Get the scheduled call date from the request
        scheduled_call_date = data.get('scheduledCallDate', '')  # Use get with default value
        campaign_name = data.get('campaignName', '')  # Use get with default value
        campaign_id = data.get('campaignId', '')  # Get campaign ID from request
        owner_name = data.get('ownerName', 'Unknown User')  # Get owner name from request

        print("campaign_id:", campaign_id)

        # Fetch campaign details from campaigns collection if campaign_id is provided
        if campaign_id:
            try:
                campaign_users_collection = get_campaign_users_collection()
                # Find the campaign by ID
                campaign = campaign_users_collection.find_one({"_id": ObjectId(campaign_id)})
                print("campaign:", campaign)
                # Find campaign by ID
                if campaign:
                    # Use campaign name from database if available
                    campaign_name = campaign.get('name', campaign_name)
                    print("campaign_name:", campaign_name)
                    
                    # If scheduled_call_date is not provided in the request, use campaign date
                    # if not scheduled_call_date:
                    scheduled_call_date = campaign.get('campaignDate', '')
                    scheduled_call_time = campaign.get('campaignTime', '')
                    
                    print(f"Retrieved campaign details - Name: {campaign_name}, Date: {scheduled_call_date}")
            except Exception as ce:
                print(f"Error fetching campaign details: {str(ce)}")
                # Continue with request data if campaign fetch fails
        
        print("scheduled_call_date:", scheduled_call_date)
        print("scheduled_call_time:", scheduled_call_time)
        print("campaign_name:", campaign_name)
        print("campaign_id:", campaign_id)
        print("owner_name:", owner_name)
        
        # Ensure users is a list
        users = data.get('users', [])
        if not isinstance(users, list):
            raise HTTPException(status_code=400, detail="Users must be a list")
        
        # Convert the incoming data format to list of ProspectIn objects
        prospects_list = []
        skipped_prospects = []
        
        for user in users:
            try:
                # Check if phone number exists and is not empty
                raw_phone = user.get('phoneNumber', '').strip()
                if not raw_phone:
                    skipped_prospects.append({
                        'name': user.get('name', 'Unknown'),
                        'reason': 'No phone number provided'
                    })
                    continue
                
                # Format phone number to ensure it has + prefix
                formatted_phone = format_phone_number(raw_phone)
                
                # Validate formatted phone number
                if not formatted_phone or formatted_phone == '+':
                    skipped_prospects.append({
                        'name': user.get('name', 'Unknown'),
                        'reason': 'Invalid phone number format'
                    })
                    continue
                
                prospect = ProspectIn(
                    name=user.get('name', '').strip() if user.get('name') else None,
                    phoneNumber=formatted_phone,
                    businessName=user.get('businessName', '').strip(),
                    email=user.get('email', '').strip(),
                    ownerName=owner_name,  # Add owner name to each prospect
                    campaignName=campaign_name,  # Add campaign name to each prospect
                    campaignId=campaign_id, # Add campaign ID (from user or request)
                    scheduledCallDate=scheduled_call_date,
                    scheduledCallTime=scheduled_call_time
                )
                prospects_list.append(prospect)
            except Exception as e:
                print(f"Error creating prospect: {str(e)}")
                skipped_prospects.append({
                    'name': user.get('name', 'Unknown'),
                    'reason': f'Error: {str(e)}'
                })
        
        print('prospects_list:', prospects_list)
        
        if not prospects_list:
            raise HTTPException(status_code=400, detail="No valid prospects provided")
            
        # Upload prospects to database
        result = upload_prospects_service(prospects_list, scheduled_call_date, campaign_name, campaign_id, scheduled_call_time)

        # Only initiate calls immediately if no scheduled date is provided
        # if result and not scheduled_call_date:
        #     create_phone_call(prospects_list)
        
        # Add information about skipped prospects to the response
        if skipped_prospects:
            result['skipped_prospects'] = {
                'count': len(skipped_prospects),
                'details': skipped_prospects
            }
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/get_prospects_by_campaign")
async def get_prospects_by_campaign_route(request: Request):
    """
    Get all prospects that belong to a specific campaign
    
    Request body:
    {
        "campaignName": "string",
        "campaignId": "string"
    }
    
    Either campaignName or campaignId must be provided
    """
    try:
        data = await request.json()
        campaign_name = data.get('campaignName')
        campaign_id = data.get('campaignId')
   
        if not campaign_name and not campaign_id:
            raise HTTPException(
                status_code=400,
                detail="Either campaign name or campaign ID is required"
            )
            
        result = get_prospects_by_campaign(campaign_name=campaign_name, campaign_id=campaign_id)
        return result
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching prospects: {str(e)}"
        )

@router.get("/initiate_call")
async def initiate_call(request: Request):
    """
    Initiate a phone call to a specific prospect
    
    Query parameters:
        phoneNumber: string - The phone number to initiate the call
        campaignId: string - The campaign ID to which the prospect belongs
    """
    try:
        # Get the phone number from query parameters
        params = dict(request.query_params)
        phone_number = params.get('phoneNumber')
        campaign_id = params.get('campaignId')
        if not phone_number or not campaign_id:
            raise HTTPException(
                status_code=400,
                detail="Phone number and campaignId is required as a query parameter"
            )
        
        # Format phone number to ensure it has the correct format (remove spaces, add + if needed)
        formatted_phone = phone_number.strip()
        if formatted_phone.startswith('+'):
            # Already has a plus sign, use as is
            pass
        elif formatted_phone.isdigit():
            # Add a plus sign to the beginning
            formatted_phone = "+" + formatted_phone
        
        # Get the prospect details
        prospect = get_prospect_by_phone_number(formatted_phone, campaign_id)
        if not prospect:
            # Try with the original phone number format if the formatted one doesn't match
            prospect = get_prospect_by_phone_number(phone_number, campaign_id)
            if not prospect:
                raise HTTPException(
                    status_code=404,
                    detail=f"Prospect with phone number {phone_number} not found"
                )
            formatted_phone = phone_number  # Use the original format if that's what was found
            
        # Create a ProspectIn object to pass to create_phone_call
        prospect_obj = ProspectIn(
            name=prospect.get('name', ''),
            phoneNumber=formatted_phone,
            businessName=prospect.get('businessName', ''),
            ownerName=prospect.get('ownerName', ''),  # Include the owner name
            campaignName=prospect.get('campaignName', ''),  # Include the campaign name
            campaignId=prospect.get('campaignId', ''),  # Include the campaign ID
        )
        print(f"prospect_obj: {prospect_obj}")
        # Initiate the call
        try:
            result = create_phone_call([prospect_obj])
            
            # return {
            #     "status": "success",
            #     "message": f"Call initiated to {formatted_phone}",
            #     "data": {
            #         "callId": result.call_id if hasattr(result, 'call_id') else None
            #     }
            # }
            logger.info(f"Total Prospects: {result['total_prospects']}, Total Batches: {result['total_batches']}, Batch Responses: {result['batch_responses']}")
        except Exception as call_error:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initiate call: {str(call_error)}"
            )
            
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error initiating call: {str(e)}"
        )

@router.post("/campaign_call")
async def initiate_campaign_calls(request: Request):
    try:
        data = await request.json()
        campaign_name = data.get("campaign_name")
        campaign_id = data.get("campaign_id")
        phone_numbers = data.get("phone_numbers", [])
        
        if not campaign_name or not phone_numbers:
            return {"error": "Campaign name and phone numbers are required"}
        
        # Create a list to store prospects that will be called
        prospects_to_call = []
        
        # Process each phone number and prepare for calling
        for phone_number in phone_numbers:
            # Format phone number using the helper function
            formatted_phone = format_phone_number(phone_number)
            
            # Get the prospect details from database
            prospect = get_prospect_by_phone_number(formatted_phone,campaign_id)
            if not prospect:
                # Try with the original format if formatted doesn't match
                prospect = get_prospect_by_phone_number(phone_number,campaign_id)
                if not prospect:
                    continue  # Skip this number if prospect not found
                formatted_phone = phone_number
            
            # Create a ProspectIn object to pass to create_phone_call
            prospect_obj = ProspectIn(
                name=prospect.get('name', ''),
                phoneNumber=formatted_phone,
                businessName=prospect.get('businessName', ''),
                ownerName=prospect.get('ownerName', ''),
                campaignName=campaign_name,
                campaignId=campaign_id
            )
            prospects_to_call.append(prospect_obj)
        
        if not prospects_to_call:
            return {"error": "No valid prospects found for the provided phone numbers"}
        
        # Initiate calls for all valid prospects
        result = create_phone_call(prospects_to_call)
        
        return {
            "success": True, 
            "message": f"Initiated calls for {len(prospects_to_call)} prospects in campaign {campaign_name}"
        }
    except Exception as e:
        return {"error": str(e)}
