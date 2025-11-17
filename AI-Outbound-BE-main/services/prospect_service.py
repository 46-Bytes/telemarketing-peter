from config.database import get_prospects_collection
import os
from models.prospect import ProspectIn
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging
import random
from models.token_model import TokenStore
from bson import ObjectId
from utils.timezone import get_brisbane_now

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def upload_prospects_service(prospects: List[ProspectIn], scheduled_call_date: str, campaign_name: str, campaign_id: str = None,scheduled_call_time: str = None):
    prospects_collection = get_prospects_collection()
    current_time = get_brisbane_now().isoformat() + "Z"
    
    # Set defaults for empty values
    if not campaign_name:
        campaign_name = "Default Campaign"
    
    # Ensure scheduled_call_date is properly formatted or None
    if not scheduled_call_date:
        scheduled_call_date = None
    
    logger.info(f"Uploading {len(prospects)} prospects to campaign '{campaign_name}' (ID: {campaign_id})")
    
    for prospect in prospects:
        # Debug logging for each prospect
        prospect_name = prospect.name or "Unknown"
        logger.info(f"Processing prospect: {prospect_name}, phone: {prospect.phoneNumber}, " +
                   f"campaign: {prospect.campaignName or campaign_name}, " +
                   f"campaignId: {prospect.campaignId or campaign_id}, " +
                   f"owner: {prospect.ownerName}")
        
        # Use prospect's campaign name/id if available, otherwise use the parameter
        prospect_campaign = prospect.campaignName if prospect.campaignName else campaign_name
        prospect_campaign_id = prospect.campaignId if prospect.campaignId else campaign_id
    
        existing_prospect = prospects_collection.find_one({"phoneNumber": prospect.phoneNumber,"campaignName": prospect.campaignName})
        
        if existing_prospect:
            logger.info(f"Updating existing prospect {prospect.phoneNumber} with campaign: {prospect.campaignName} (ID: {prospect.campaignId})")
            prospects_collection.update_one(
                {"phoneNumber": prospect.phoneNumber, "campaignName": prospect.campaignName},
                {
                        "$set": {
                            "campaignName": prospect_campaign,
                            "campaignId": prospect_campaign_id,
                            "businessName": prospect.businessName,
                            "scheduledCallDate": scheduled_call_date,
                            "scheduledCallTime": scheduled_call_time,
                            "ownerName": prospect.ownerName,
                            "status": "new",
                            "retryCount": 0,
                            "callBackCount": 0,
                            "isCallBack": None,
                            "callBackDate": None,
							"callBackTime": None,
                            "isEbook": None,
                            "updatedAt": {"$date": current_time},
                            "appointment": {
                                "appointmentInterest": None,
                                "appointmentDateTime": None,
                            },
                        }
                    }
                )
            continue
            # else:
            #     # If the phone number exists but with a different campaign, log this but we'll try to handle it differently
            #     logger.info(f"Prospect with phone {prospect.phoneNumber} exists but in a different campaign. Current prospect's campaign: {prospect_campaign}, existing campaign: {existing_prospect.get('campaignName')}")
            #     # We'll attempt to modify the document with campaign info below
            #     try:
            #         # Update the existing document with new campaign info
            #         # This keeps the same prospect but changes their campaign
            #         prospects_collection.update_one(
            #             {"phoneNumber": prospect.phoneNumber},
            #             {
            #                 "$set": {
            #                     "campaignName": prospect_campaign,
            #                     "campaignId": prospect_campaign_id,
            #                     "businessName": prospect.businessName,
            #                     "scheduledCallDate": scheduled_call_date,
            #                     "ownerName": prospect.ownerName,
            #                     "status": "new",
            #                     "retryCount": 0,
            #                     "callBackCount": 0,
            #                     "isCallBack": None,
            #                     "callBackDate": None,
            #                     "isEbook": None,
            #                     "updatedAt": {"$date": current_time},
            #                     "appointment": {
            #                         "appointmentInterest": None,
            #                         "appointmentDateTime": None,
            #                     },
            #                 }
            #             }
            #         )
            #         continue
            #     except Exception as e:
            #         logger.error(f"Error updating prospect with new campaign: {str(e)}")
            #         raise

        else:
            # Insert new prospect if no matching record exists
            logger.info(f"Creating new prospect with phone: {prospect.phoneNumber}, campaign: {prospect_campaign}")
            try:
                result = prospects_collection.insert_one({
                    "name": prospect.name,
                    "phoneNumber": prospect.phoneNumber,
                    "businessName": prospect.businessName,
                    "ownerName": prospect.ownerName,
                    "email": None,
                    "status": "new",
                    "retryCount": 0,
                    "callBackCount": 0,
                    "isCallBack": None,
                    "callBackDate": None,
					"callBackTime": None,
                    "isEbook": None,
                    "isNewsletterSent": None,
                    "scheduledCallDate": scheduled_call_date,
                    "scheduledCallTime": scheduled_call_time,
                    "campaignName": prospect_campaign,
                    "campaignId": prospect_campaign_id,
                    "createdAt": {"$date": current_time},
                    "updatedAt": {"$date": current_time},
                    "appointment": {
                        "appointmentInterest": None,
                        "appointmentDateTime": None,
                    },
                    "calls": [],
                    "auditLogs": [],
                })
                logger.info(f"Created new prospect with phone: {prospect.phoneNumber}, campaign: {prospect_campaign}")
            except Exception as e:
                logger.error(f"Error creating prospect: {str(e)}")
                raise
                
    return {
        "message": "Prospects Added successfully",
    }

from services.report_service import update_outcome_fields, update_dynamic_fields, are_all_outcomes_complete, finalize_and_send


async def update_prospect_call_info(webhook_data: Dict[Any, Any]):
    """Update prospect information with call details from webhook - handles both individual and batch calls"""
    try:
        logger.info(f"Updating prospect call info for webhook data: {webhook_data}")
        collection = get_prospects_collection()
        call_data = webhook_data.get('call', {})
        
        # Extract required information from webhook data
        call_status = call_data.get('call_status', 'unknown')
        disconnection_reason = call_data.get('disconnection_reason')
        
        # Map call status to our internal status
        if call_status == "error" and disconnection_reason:
            mapped_status = disconnection_reason
        else:
            mapped_status = call_status
            
        call_info = {
            "timestamp": datetime.fromtimestamp(call_data.get('start_timestamp', 0) / 1000).isoformat() + "Z",
            "duration": call_data.get('duration_ms', 0) / 1000,
            "status": mapped_status,
            "recordingUrl": call_data.get('recording_url'),
            "transcript": call_data.get('transcript'),
            "callSummary": call_data.get('call_analysis', {}).get('custom_analysis_data', {}).get('call_summary_info')
        }

        # Get the existing prospect data first
        to_number = call_data.get('to_number', '')
        call_id = call_data.get('call_id')
        campaign_id = call_data.get('retell_llm_dynamic_variables', {}).get('campaign_id')
        
        # For batch calls, we need to find the prospect by phone number and campaign ID
        # and look for a call entry with batchId (not callId)
        existing_prospect = collection.find_one({
            "phoneNumber": to_number,
            "campaignId": campaign_id
        })
        
        if not existing_prospect:
            logger.warning(f"No prospect found for phone {to_number} in campaign {campaign_id}")
            return {"message": "Prospect not found"}
        
        # Check if this is a batch call by looking for the most recent batch call entry
        batch_call_entry = None
        calls = existing_prospect.get('calls', [])
        
        # Find the most recent batch call entry (last one in the array)
        for call_entry in reversed(calls):
            if call_entry.get('batchId') and not call_entry.get('callId'):
                batch_call_entry = call_entry
                break
        
        if batch_call_entry:
            # This is a batch call - we need to replace the batch entry with detailed call info
            call_info.update({
                "callId": call_id,
                "batchId": batch_call_entry.get('batchId')
            })
            
            logger.info(f"Found batch call entry: {batch_call_entry.get('batchId')} for prospect {to_number}")
            
            # Update the call entry by replacing the batch entry
            update_result = collection.update_one(
                {
                    "phoneNumber": to_number,
                    "campaignId": campaign_id,
                    "calls.batchId": batch_call_entry.get('batchId')
                },
                {
                    "$set": {"calls.$": call_info}
                }
            )
            
            if update_result.modified_count > 0:
                logger.info(f"Successfully updated batch call entry for prospect {to_number} with call details")
            else:
                logger.warning(f"Failed to update batch call entry for prospect {to_number}")
                # Fallback: try to add the call directly
                collection.update_one(
                    {"phoneNumber": to_number, "campaignId": campaign_id},
                    {"$push": {"calls": call_info}}
                )
                logger.info(f"Added call directly to prospect {to_number}")
        else:
            # This is an individual call - find by callId
            existing_prospect = collection.find_one({
                "phoneNumber": to_number,
                "campaignId": campaign_id,
                "calls.callId": call_id
            })
            
            if not existing_prospect:
                logger.warning(f"No call found with callId {call_id} for prospect {to_number}")
                return {"message": "Call not found"}

        # Handle appointment info
        new_appointment_interest = call_data.get('call_analysis', {}).get('custom_analysis_data', {}).get('appointment_interest')
        new_appointment_datetime = call_data.get('call_analysis', {}).get('custom_analysis_data', {}).get('appointment_date_time')
        
        # Extract appointment type from transcript
        transcript = call_data.get('transcript', '').lower()
        appointment_type = None
        
        # Check for appointment type in transcript with more variations
        if any(phrase in transcript for phrase in ['selling appointment', 'sales appointment', 'book selling', 'book a selling', 
                                                 'selling meeting', 'sales meeting', 'selling consultation']):
            appointment_type = 'selling'
        elif any(phrase in transcript for phrase in ['advisory appointment', 'sales advisory appointment', 'book advisory', 
                                                   'book an advisory', 'advisory meeting', 'advisory consultation']):
            appointment_type = 'advisory'
        
        # Check for agent questions about appointment type preferences
        if appointment_type is None and new_appointment_interest is True:
            # If agent asks about type preference and user responds with a preference
            if ('would you prefer selling' in transcript or 'would you like selling' in transcript or 
                'selling or advisory' in transcript or 'sales or advisory' in transcript):
                # Look for user's response after the question
                if 'selling' in transcript.split('selling or advisory')[-1]:
                    appointment_type = 'selling'
                elif 'advisory' in transcript.split('selling or advisory')[-1]:
                    appointment_type = 'advisory'
                elif 'sales' in transcript.split('sales or advisory')[-1]:
                    appointment_type = 'selling'
                else:
                    # Default to selling if there's appointment interest but type is unclear
                    appointment_type = 'selling'
        
        # If appointment type couldn't be determined but there's appointment interest, default to 'selling'
        if appointment_type is None and new_appointment_interest is True:
            appointment_type = 'selling'
        
        # Get existing appointment info
        existing_appointment = existing_prospect.get('appointment', {})
            
        appointment_info = {
            "appointmentInterest": new_appointment_interest if (existing_appointment.get('appointmentInterest') is None or existing_appointment.get('appointmentInterest') is False) else existing_appointment.get('appointmentInterest'),
            "appointmentDateTime": new_appointment_datetime if (existing_appointment.get('appointmentInterest') is None or existing_appointment.get('appointmentInterest') is False) else existing_appointment.get('appointmentDateTime'),
            "appointmentType": appointment_type if (existing_appointment.get('appointmentType') is None) else existing_appointment.get('appointmentType'),
            "meetingLink": existing_appointment.get('meetingLink') if (existing_appointment.get('meetingLink') is not None) else None
        }

        # Handle callback date
        call_back_request = call_data.get('call_analysis', {}).get('custom_analysis_data', {}).get('call_back_request')
        new_call_back_date = None
        new_call_back_time = None
        
        # Get the callback date from analysis
        analysis_callback_date = call_data.get('call_analysis', {}).get('custom_analysis_data', {}).get('call_back_date', '')
        analysis_callback_time = call_data.get('call_analysis', {}).get('custom_analysis_data', {}).get('call_back_time', '')

        if call_back_request is True and analysis_callback_date:
            # Validate if the date is in YYYY-MM-DD format
            try:
                datetime.strptime(analysis_callback_date, '%Y-%m-%d')
                new_call_back_date = analysis_callback_date
            except ValueError:
                # If date format is invalid, set to tomorrow
                new_call_back_date = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')
            # Optional time (HH:MM 24h)
            if isinstance(analysis_callback_time, str) and len(analysis_callback_time) in (4,5):
                new_call_back_time = analysis_callback_time
        elif call_back_request is None:
            # If call not picked up, set to tomorrow with random time (10 AM - 7 PM)
            new_call_back_date  = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')
            # Generate random time between 10:00 and 18:59 (business hours)
            random_hour = random.randint(10, 18)
            random_minute = random.randint(0, 59)
            new_call_back_time = f"{random_hour:02d}:{random_minute:02d}"
        elif call_back_request is False:
            # If user explicitly doesn't want a callback
            new_call_back_date = None
            new_call_back_time = None

        if existing_prospect:
            existing_is_callback = existing_prospect.get('isCallBack')
            existing_callback_date = existing_prospect.get('callBackDate')
            existing_callback_time = existing_prospect.get('callBackTime')
            
            # Only update if current values are None/False or if we have a new valid callback request
            if (existing_is_callback is None or existing_is_callback is False) or call_back_request is True:
                call_back_date = new_call_back_date
                call_back_time = new_call_back_time if new_call_back_time is not None else existing_callback_time
                is_callback = call_back_request
            else:
                call_back_date = existing_callback_date
                call_back_time = existing_callback_time
                is_callback = existing_is_callback
        else:
            call_back_date = new_call_back_date
            call_back_time = new_call_back_time
            is_callback = call_back_request

        # Handle ebook
        new_ebook = call_data.get('call_analysis', {}).get('custom_analysis_data', {}).get('ebook')
        if existing_prospect:
            existing_ebook = existing_prospect.get('isEbook')
            is_ebook = new_ebook if (existing_ebook is None or existing_ebook is False) else existing_ebook
        else:
            is_ebook = new_ebook

        # determine if the prospect is subscribed to the newsletter
        is_newsletter_sent = call_data.get('call_analysis', {}).get('custom_analysis_data', {}).get('is_subscribe_to_news_letter')
        email = call_data.get('call_analysis', {}).get('custom_analysis_data', {}).get('email')
        
        # Create audit log entry
        audit_log = {
            "actionType": "Call Completed",
            "performedBy": "AI Agent",
            "timestamp": {"$date": get_brisbane_now().isoformat() + "Z"},
            "details": {
                "callId": call_id,
                "status": call_info['status'],   
            }
        }

        # Map call status to prospect status
        call_status = call_data.get('call_status', 'unknown')
        if call_status == "ended":
            prospect_status = "picked_up"
        elif call_status in ["busy", "no_answer", "voicemail"]:
            prospect_status = "contacted"
        else:
            prospect_status = "error"
            
        # Create update dictionary for prospect-level fields
        prospect_update_dict = {
            "scheduledCallDate": new_call_back_date,
            "email": email,
            "status": prospect_status,
            "isCallBack": is_callback,
            "callBackDate": call_back_date,
		    "callBackTime": call_back_time,
            "appointment": appointment_info,
            "updatedAt": {"$date": get_brisbane_now().isoformat() + "Z"},
            "isEbook": is_ebook,
            "isNewsletterSent": is_newsletter_sent
        }

        # Only add retryCount reset and increment callBackCount if call_back_date is in YYYY-MM-DD format
        if analysis_callback_date and isinstance(analysis_callback_date, str) and len(analysis_callback_date) == 10:
            try:
                datetime.strptime(analysis_callback_date, '%Y-%m-%d')
                prospect_update_dict["retryCount"] = 1
            except ValueError:
                pass

        if batch_call_entry:
            # For batch calls, update the prospect and the call entry separately
            # First update the prospect-level fields
            collection.update_one(
                {
                    "phoneNumber": to_number,
                    "campaignId": campaign_id
                },
                {
                    "$set": prospect_update_dict,
                    "$push": {"auditLogs": audit_log}
                }
            )
            
            # Then update the call entry with detailed call info
            collection.update_one(
                {
                    "phoneNumber": to_number,
                    "campaignId": campaign_id,
                    "calls.batchId": batch_call_entry.get('batchId')
                },
                {
                    "$set": {
                        "calls.$.timestamp": call_info['timestamp'],
                        "calls.$.duration": call_info['duration'],
                        "calls.$.status": call_info['status'],
                        "calls.$.recordingUrl": call_info['recordingUrl'],
                        "calls.$.callSummary": call_info['callSummary'],
                        "calls.$.transcript": call_info['transcript'],
                        "calls.$.callId": call_id
                    }
                }
            )
            
            # Increment callBackCount if needed
            if analysis_callback_date and isinstance(analysis_callback_date, str) and len(analysis_callback_date) == 10:
                try:
                    datetime.strptime(analysis_callback_date, '%Y-%m-%d')
                    collection.update_one(
                        {
                            "phoneNumber": to_number,
                            "campaignId": campaign_id
                        },
                        {
                            "$inc": {"callBackCount": 1}
                        }
                    )
                except ValueError:
                    pass
                    
        else:
            # For individual calls, use the original logic
            call_update_dict = {
                "calls.$.timestamp": call_info['timestamp'],
                "calls.$.duration": call_info['duration'],
                "calls.$.status": call_info['status'], 
                "calls.$.recordingUrl": call_info['recordingUrl'],
                "calls.$.callSummary": call_info['callSummary'],
                "calls.$.transcript": call_info['transcript']
            }
            
            # Combine prospect and call updates
            update_dict = {**prospect_update_dict, **call_update_dict}
            update_dict["auditLogs.$[log].details.status"] = audit_log["details"]["status"]
            
            # Update the specific call record in the calls array and add audit log
            result = collection.update_one(
                {
                    "phoneNumber": to_number,
                    "calls.callId": call_id,
                    "campaignId": campaign_id
                },
                {
                    "$set": update_dict,
                    "$push": {"auditLogs": audit_log}
                },
                array_filters=[
                    {"log.details.callId": call_id}
                ]
            )
            
            # Increment callBackCount if needed
            if analysis_callback_date and isinstance(analysis_callback_date, str) and len(analysis_callback_date) == 10:
                try:
                    datetime.strptime(analysis_callback_date, '%Y-%m-%d')
                    collection.update_one(
                        {
                            "phoneNumber": to_number,
                            "calls.callId": call_id,
                            "campaignId": campaign_id
                        },
                        {
                            "$inc": {"callBackCount": 1}
                        }
                    )
                except ValueError:
                    pass

        # Update report CSV with connection and outcome
        try:
            # Only update connection/outcome here; dynamic fields are set via explicit route
            analysis = call_data.get('call_analysis', {}).get('custom_analysis_data', {})
            call_connection = mapped_status
            explicit_outcome = analysis.get('call_outcome')
            call_outcome = explicit_outcome
            if not call_outcome:
                summary = (analysis.get('call_summary_info') or '')
                lower = summary.lower()
                if 'no interest' in lower:
                    call_outcome = 'no interest'
                elif 'ebook' in lower:
                    call_outcome = 'interested in ebook'
                elif 'meeting' in lower or 'appointment' in lower:
                    call_outcome = 'meeting booked'
                elif 'hung up' in lower:
                    call_outcome = 'user hung up'
                else:
                    call_outcome = mapped_status

            if campaign_id:
                update_outcome_fields(campaign_id, to_number, call_connection, call_outcome)

                # Finalize/email if all outcomes complete; leave dynamic fields untouched
                try:
                    if are_all_outcomes_complete(campaign_id):
                        recipient = os.getenv('REPORT_RECIPIENT_EMAIL') or os.getenv('SMTP_USER_EMAIL')
                        if recipient:
                            finalize_and_send(campaign_id, recipient, subject=f"Campaign {campaign_id} Report")
                except Exception as _e:
                    logger.warning(f"Finalize/email skipped for campaign {campaign_id}: {_e}")
        except Exception as _e:
            logger.warning(f"Report update skipped for {to_number}: {_e}")

        logger.info(f"Successfully updated prospect call information for phone number: {to_number}")
        return {"message": "Prospect call information updated successfully"}

    except Exception as e:
        logger.error(f"Error updating prospect call information: {str(e)}")
        raise

def get_prospect_details_by_phone_number_and_campaign_id(phone_number: str, campaign_id: str = None):
    collection = get_prospects_collection()
    prospect = collection.find_one({"phoneNumber": phone_number, "campaignId": campaign_id})
    if prospect:
        prospect["_id"] = str(prospect["_id"])
        return prospect
    else:
        return {"message": "Prospect not found"}

def get_prospects_by_campaign(campaign_name: str = None, campaign_id: str = None):
    """
    Get all prospects that belong to a specific campaign
    
    Args:
        campaign_name (str, optional): Name of the campaign to filter prospects
        campaign_id (str, optional): ID of the campaign to filter prospects
        
    Returns:
        dict: List of prospects and total count
    """
    try:
        collection = get_prospects_collection()
        
        # Build the query based on available parameters
        query = {}
        if campaign_id:
            query["campaignId"] = campaign_id
        elif campaign_name:
            query["campaignName"] = campaign_name
        else:
            raise ValueError("Either campaign_name or campaign_id must be provided")
        
        # Find all prospects that have this campaign
        prospects = list(collection.find(query))
        
        # Convert ObjectId to string for JSON serialization
        for prospect in prospects:
            prospect["_id"] = str(prospect["_id"])
        
        return {
            "status": "success",
            "message": "Prospects retrieved successfully",
            "data": {
                "prospects": prospects,
                "total": len(prospects)
            }
        }
    except Exception as e:
        logger.error(f"Error fetching prospects for campaign (name: {campaign_name}, id: {campaign_id}): {str(e)}")
        raise

def get_prospect_by_phone_number(phone_number, campaign_id=None):
    """
    Get a prospect by phone number
    
    Args:
        phone_number (str): The phone number to search for
        campaign_id (str): The campaign ID to filter prospects
        
    Returns:
        dict: The prospect document or None if not found
    """
    collection = get_prospects_collection()
    
    # Find the prospect by phone number
    prospect = collection.find_one({"phoneNumber": phone_number, "campaignId": campaign_id})
    
    return prospect

def update_prospect_appointment(phone_number: str, appointment_interest: bool, appointment_date_time: str = None, meeting_link: str = None, campaign_id: str = None, appointment_type: str = None):
    """
    Update a prospect's appointment information including Microsoft meeting webLink
    
    Args:
        phone_number (str): The phone number of the prospect
        campaign_id (str): The campaign ID to filter prospects
        appointment_interest (bool): Whether the prospect is interested in an appointment
        appointment_date_time (str, optional): ISO format date-time for the appointment
        meeting_link (str, optional): Web link to the Microsoft meeting
        appointment_type (str, optional): Type of appointment ('selling' or 'advisory')
        
    Returns:
        dict: Success message or error
    """
    try:
        print("web link in final call:", meeting_link)
        collection = get_prospects_collection()
        
        # First check if the prospect exists
        existing_prospect = collection.find_one({"phoneNumber": phone_number, "campaignId": campaign_id})
        if not existing_prospect:
            return {"status": "error", "message": f"Prospect with phone number {phone_number} not found"}
        
        # Create appointment info object with webLink
        appointment_info = {
            "appointmentInterest": appointment_interest,
            "appointmentDateTime": appointment_date_time,
            "meetingLink": meeting_link,  # Add the webLink from Microsoft
            "appointmentType": appointment_type  # Add the appointment type
        }

        print("appointment_info in final call:", appointment_info)
        
        # Update prospect
        update_result = collection.update_one(
            {"phoneNumber": phone_number, "campaignId": campaign_id},
            {
                "$set": {
                    "appointment": appointment_info,
                    "status": "picked_up",  # Update status to picked_up when appointment is scheduled
                    "updatedAt": {"$date": get_brisbane_now().isoformat() + "Z"}
                }
            }
        )
        
        # Create an audit log entry
        audit_log = {
            "actionType": "Appointment Updated",
            "performedBy": "User",
            "timestamp": {"$date": get_brisbane_now().isoformat() + "Z"},
            "details": {
                "appointmentInterest": appointment_interest,
                "appointmentDateTime": appointment_date_time,
                "meetingLink": meeting_link,
                "appointmentType": appointment_type
            }
        }
        
        # Add the audit log entry
        collection.update_one(
            {"phoneNumber": phone_number, "campaignId": campaign_id},
            {"$push": {"auditLogs": audit_log}}
        )
        
        if update_result.modified_count > 0:
            return {
                "status": "success", 
                "message": "Appointment updated successfully"
            }
        else:
            return {
                "status": "error", 
                "message": "Failed to update appointment"
            }
            
    except Exception as e:
        logger.error(f"Error updating appointment for prospect {phone_number}: {str(e)}")
        raise
