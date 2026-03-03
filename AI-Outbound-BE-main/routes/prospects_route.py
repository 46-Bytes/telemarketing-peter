# API routes

from datetime import datetime
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Request
from typing import List
from models.prospect import ProspectIn
from services.call_initiation_service import create_phone_call
from services.report_service import seed_rows_if_missing, update_dynamic_fields, save_report_locally
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
    
    # Ensure + prefix so the number is stored and sent with + everywhere
    if not cleaned.startswith('+'):
        cleaned = '+' + cleaned

    if cleaned.startswith('+92'):
        return cleaned

    # Handle Australian phone number formatting
    digits_only = cleaned[1:] if cleaned.startswith('+') else cleaned

    if digits_only.startswith('0'):
        cleaned = '+61' + digits_only[1:]
    elif len(digits_only) == 9:
        cleaned = '+61' + digits_only
    elif len(digits_only) == 10 and not digits_only.startswith('61'):
        cleaned = '+6' + digits_only

    # Final safeguard: ensure output always has + prefix when non-empty
    if cleaned and not cleaned.startswith('+'):
        cleaned = '+' + cleaned
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
    Initiate a phone call to a specific prospect (Call Now button).

    Query parameters:
        phoneNumber: string - The phone number to initiate the call
        campaignId: string - The campaign ID to which the prospect belongs
    """
    try:
        params = dict(request.query_params)
        phone_number = params.get('phoneNumber')
        campaign_id = params.get('campaignId')
        logger.info("[CALL] /initiate_call requested | phone=%s | campaign_id=%s", phone_number, campaign_id)
        if not phone_number or not campaign_id:
            raise HTTPException(
                status_code=400,
                detail="Phone number and campaignId is required as a query parameter"
            )
        
        # Normalize phone: add + if missing, strip, so we store and use it consistently
        formatted_phone = format_phone_number(phone_number.strip()) if phone_number else ""
        if not formatted_phone or formatted_phone == '+':
            raise HTTPException(status_code=400, detail="Invalid phone number")

        # Get the prospect details
        prospect = get_prospect_by_phone_number(formatted_phone, campaign_id)
        if not prospect:
            prospect = get_prospect_by_phone_number(phone_number.strip(), campaign_id)
            if not prospect:
                raise HTTPException(
                    status_code=404,
                    detail=f"Prospect with phone number {phone_number} not found"
                )
            # Use stored number normalized with + so we send it with + further
            formatted_phone = format_phone_number(prospect.get("phoneNumber", "")) or formatted_phone
            
        # Create a ProspectIn object to pass to create_phone_call
        prospect_obj = ProspectIn(
            name=prospect.get('name', ''),
            phoneNumber=formatted_phone,
            businessName=prospect.get('businessName', ''),
            ownerName=prospect.get('ownerName', ''),  # Include the owner name
            campaignName=prospect.get('campaignName', ''),  # Include the campaign name
            campaignId=prospect.get('campaignId', ''),  # Include the campaign ID
        )
        logger.info("[CALL] Initiated from Call Now | phone=%s | campaign_id=%s", formatted_phone, campaign_id)
        try:
            result = await create_phone_call([prospect_obj], source="call_now")
            logger.info("[CALL] Call Now completed | phone=%s | batches=%s", formatted_phone, result.get('total_batches', 0))
            return result
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
        
        # # Seed report rows for this campaign (ensure all prospects exist in temp CSV)
        # try:
        #     seed_rows_if_missing(
        #         campaign_id=campaign_id,
        #         prospects=[
        #             {
        #                 "name": p.name or "",
        #                 "phoneNumber": p.phoneNumber,
        #                 "businessName": p.businessName or "",
        #             }
        #             for p in prospects_to_call
        #         ],
        #     )
        # except Exception as _e:
        #     # Do not fail call initiation if reporting seed fails
        #     logger.warning(f"Report seed failed for campaign {campaign_id}: {_e}")

        # Initiate calls for all valid prospects
        result = await create_phone_call(prospects_to_call, source="campaign_call")
        return {
            "success": True, 
            "message": f"Initiated calls for {len(prospects_to_call)} prospects in campaign {campaign_name}"
        }
    except Exception as e:
        return {"error": str(e)}

@router.post("/add_newowner_contact")
async def add_newowner_contact(request: Request):
    """
    Explicitly update Retell-provided fields for a prospect row in the temporary report.
    Payload JSON:
      - campaignId: string (required)
      - phoneNumber: string (required)
      - newOwnerName: string (optional)
      - newNumber: string (optional)
      - bestTimeToCall: string (optional)
    """
    try:
        data = await request.json()
        # Retell may send tool args at top level or nested under "arguments" / "args"
        payload = data.get("arguments") or data.get("args") or data
        campaign_id = payload.get("campaign_id") or payload.get("campaignId")
        phone_number = payload.get("phoneNumber")
        new_owner_name = payload.get("newOwnerName")
        new_number = payload.get("newNumber")
        best_time_to_call = payload.get("bestTimeToCall")

        if not campaign_id or not phone_number:
            logger.warning("[AddNewOwner] 400 - missing campaign_id or phoneNumber. Raw body keys: %s", list(data.keys()))
            raise HTTPException(status_code=400, detail="campaign_id and phoneNumber are required")

        logger.info(f"AddNewOwner called for campaign {campaign_id}, phone {phone_number}")
        logger.info(f"New owner data - Name: {new_owner_name}, Number: {new_number}, Best time: {best_time_to_call}")

        # Update the report CSV with new owner data
        update_dynamic_fields(
            campaign_id=campaign_id,
            phone_number=phone_number,
            new_owner_name=new_owner_name,
            new_number=new_number,
            best_time_to_call=best_time_to_call,
        )

        # Also generate/update a local XLSX file that you can open easily
        try:
            local_path = save_report_locally(campaign_id)
            if local_path:
                logger.info(f"Local new-owner report XLSX updated at {local_path}")
        except Exception as e:
            logger.warning(f"Failed to generate local XLSX report for campaign {campaign_id}: {e}")

        # # Also update the prospect in MongoDB with new owner data
        # from services.prospect_service import get_prospects_collection
        # collection = get_prospects_collection()
        
        # update_data = {}
        # if new_owner_name:
        #     update_data["newOwnerName"] = new_owner_name
        # if new_number:
        #     update_data["newOwnerPhone"] = new_number
        # if best_time_to_call:
        #     update_data["bestTimeToCall"] = best_time_to_call
        
        # if update_data:
        #     result = collection.update_one(
        #         {"phoneNumber": phone_number, "campaignId": campaign_id},
        #         {"$set": update_data}
        #     )
        #     logger.info(f"Updated prospect in MongoDB: {result.modified_count} document(s) modified")

        return {"success": True, "message": "New owner data captured successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in AddNewOwner: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error updating new owner data: {str(e)}")
