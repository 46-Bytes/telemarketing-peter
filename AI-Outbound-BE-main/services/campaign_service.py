from fastapi import HTTPException
from config.database import get_campaign_users_collection, get_campaigns_collection, get_users_collection, get_prospects_collection
from pymongo.errors import DuplicateKeyError
from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel

def create_new_campaign(campaign_name: str, users: str, campaignDate: str = None, description: str = None, has_ebook: bool = False, campaignTime: str = None):
    try:
        campaign_users_collection = get_campaign_users_collection()
        users_collection = get_users_collection()
        
        new_campaign = {
            "campaignName": campaign_name,
            "description": description,
            "users": users,
            "campaignDate": campaignDate,
            "campaignTime": campaignTime,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "maxRetry": 3,
            "isVisible": True,
            "has_ebook": has_ebook
        }
        print("New campaign:", new_campaign)
        
        result = campaign_users_collection.insert_one(new_campaign)
        created_campaign = campaign_users_collection.find_one({"_id": result.inserted_id})
        campaign_id = str(created_campaign["_id"])
        
        # Update each user in the users list by adding this campaign_id to their campaign_user_ids array
        # if users and len(users) > 0:
            # for user_id in users:
                # Add the campaign_user_id to the user's campaign_user_ids array using $addToSet
                # # $addToSet ensures no duplicate campaign_user_ids
                # users_collection.update_one(
                #     {"_id": ObjectId(user_id)},
                #     {"$addToSet": {"campaign_user_ids": campaign_id}}
                # )
        
        return {
            "status": "success",
            "message": "Campaign created successfully",
            "data": {
                "id": campaign_id,
                "campaignName": created_campaign["campaignName"],
                "description": created_campaign.get("description"),
                "users": created_campaign["users"],
                "campaignTime": created_campaign["campaignTime"],
                "maxRetry": 3,
                "isVisible": True,
                "created_at": created_campaign["created_at"],
                "updated_at": created_campaign["updated_at"],
                "has_ebook": created_campaign["has_ebook"]
            }
        }
    except DuplicateKeyError:
        raise HTTPException(
            status_code=400,
            detail=f"Campaign with name '{campaign_name}' already exists"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while creating the campaign: {str(e)}"
        )

def getCampaigns():
    try:
        campaign_collection = get_campaigns_collection()
        campaigns = list(campaign_collection.find({"isVisible": True}))
        transformed_campaigns = [{
            "id": str(campaign["_id"]),
            "campaignName": campaign.get("campaignName"),
            "description": campaign.get("description"),
            "owner_id": campaign.get("owner_id"),
            "users": campaign.get("users", []),
            "businessName": campaign.get("businessName"),
            "fullname": campaign.get("fullname"),
            "email": campaign.get("email"),
            "has_ebook": campaign.get("has_ebook", False),
            "ebook_path": campaign.get("ebook_path"),
            "created_at": campaign.get("created_at"),
            "maxRetry": campaign.get("maxRetry"),
            "isVisible": campaign.get("isVisible"),
            "updated_at": campaign.get("updated_at")
        } for campaign in campaigns]
        return {
            "status": "success",
            "message": "Campaigns retrieved successfully",
            "data": transformed_campaigns
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching campaigns: {str(e)}"
        )

def update_campaign_ebook(campaign_id: str, ebook_path: str):
    try:
        campaign_collection = get_campaigns_collection()
        
        # Update campaign with ebook information
        result = campaign_collection.update_one(
            {"_id": ObjectId(campaign_id)},
            {
                "$set": {
                    "has_ebook": True,
                    "ebook_path": ebook_path,
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Campaign with ID {campaign_id} not found"
            )
            
        return {
            "status": "success",
            "message": "Campaign ebook information updated successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while updating campaign ebook information: {str(e)}"
        )

def get_brokers():
    try:
        users_collection = get_users_collection()
        brokers = list(users_collection.find({"role": "user"}))
        return [
            {
                "id": str(broker["_id"]),
                "name": broker.get("name"),
                "email": broker.get("email"),
                "role": broker.get("role")
            }
            for broker in brokers
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching brokers: {str(e)}"
        )
    
def getCampaignUsers():
    try:
        print("Getting campaign users")
        campaign_users_collection = get_campaign_users_collection()
        users_collection = get_users_collection()
        print("Campaign users collection:", campaign_users_collection)
        campaign_users = list(campaign_users_collection.find({"isVisible": True}))
        print("Campaign users:", campaign_users)
        
        transformed_campaign_users = []
        for campaign_user in campaign_users:
            # Get user information if users field exists
            owner_name = None
            owner_email = None
            if campaign_user.get("users"):
                user = users_collection.find_one({"_id": ObjectId(campaign_user["users"])})
                if user:
                    owner_name = user.get("name")
                    owner_email = user.get("email")
            
            transformed_campaign_users.append({ 
                "id": str(campaign_user["_id"]),
                "campaignName": campaign_user.get("campaignName"),
                "description": campaign_user.get("description"),
                "users": campaign_user.get("users"),
                "owner_name": owner_name,
                "owner_email": owner_email,
                "prospects": campaign_user.get("prospects", []),
                "campaignDate": campaign_user.get("campaignDate"),
                "campaignTime": campaign_user.get("campaignTime"),
                "created_at": campaign_user.get("created_at"),
                "updated_at": campaign_user.get("updated_at"),
                "hasEbook": campaign_user.get("has_ebook"),
                "maxRetry": campaign_user.get("maxRetry"),
                "ebookPath": campaign_user.get("ebook_path")
            })
            
        return {
            "status": "success",
            "message": "Campaign users retrieved successfully",
            "data": transformed_campaign_users
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

def get_campaigns_by_user_id(user_id: str):
    try:
        #users_collection = get_users_collection()
        campaign_users_collection = get_campaign_users_collection()
        
        # Get the user document to find their campaign_user_ids
        user = get_users_collection().find_one({"_id": ObjectId(user_id)})
        # if not user or "campaign_user_ids" not in user or not user["campaign_user_ids"]:
        #     return {
        #         "status": "success",
        #         "message": "No campaigns found for this user",
        #         "data": []
        #     }

        print("User:", user)
        
        # Convert ObjectId to string for each campaign ID
        # campaign_ids = [ObjectId(campaign_id) for campaign_id in user["campaign_user_ids"]]
        
        # Fetch all campaigns where _id is in the user's campaign_user_ids
        # campaigns = list(campaign_users_collection.find({"_id": {"$in": campaign_ids}}))
        campaigns = list(campaign_users_collection.find({"users": user_id}))
        transformed_campaigns = [{
            "id": str(campaign["_id"]),
            "campaignName": campaign.get("campaignName"),
            "description": campaign.get("description"),
            "users": campaign.get("users"),
            "maxRetry": campaign.get("maxRetry"),
            "owner_id": campaign.get("owner_id"),
            "owner_name": user.get("name"),
            "owner_email": user.get("email"),
            # "prospects": campaign.get("prospects", []),
            "campaignDate": campaign.get("campaignDate"),
            "created_at": campaign.get("created_at"),
            "updated_at": campaign.get("updated_at"),
            "hasEbook": campaign.get("has_ebook"),
            "ebookPath": campaign.get("ebook_path")
        } for campaign in campaigns]
        
        return {
            "status": "success",
            "message": "Campaigns retrieved successfully",
            "data": transformed_campaigns
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred while fetching user campaigns: {str(e)}"
        )

def get_prospects_for_campaign(campaign_id: str):
    try:
        campaign_users_collection = get_campaign_users_collection()
        prospects_collection = get_prospects_collection()
        
        # Find the campaign
        campaign = campaign_users_collection.find_one({"_id": ObjectId(campaign_id)})
        if not campaign:
            raise HTTPException(
                status_code=404,
                detail=f"Campaign with ID {campaign_id} not found"
            )
            
        # # Get prospect IDs from the campaign
        # prospect_ids = campaign.get("prospects", [])
        
        # if not prospect_ids:
        #     return {
        #         "status": "success",
        #         "message": "No prospects found for this campaign",
        #         "data": []
        #     }
            
        # Convert prospect IDs to ObjectId
        # prospect_object_ids = [ObjectId(pid) for pid in prospect_ids]
        
        # Fetch prospects from prospects collection
        prospects = list(prospects_collection.find({"campaignId": campaign_id}))
        
        # Transform prospects data
        transformed_prospects = []
        for prospect in prospects:
            transformed_prospect = {
                "id": str(prospect["_id"]),
                "name": prospect.get("name"),
                "phoneNumber": prospect.get("phoneNumber"),
                "businessName": prospect.get("businessName"),
                "status": prospect.get("status"),
                "email": prospect.get("email"),
                "ownerName": prospect.get("ownerName"),
                "createdAt": prospect.get("createdAt"),
                "campaignId": prospect.get("campaignId"),
                "campaignName": prospect.get("campaignName"),
                "scheduledCallDate": prospect.get("scheduledCallDate"),
                "calls": prospect.get("calls"),
                "appointment": prospect.get("appointment"),
                "status": prospect.get("status"),
                "scheduledCallTime": prospect.get("scheduledCallTime"),
                # Add other fields as needed
            }
            transformed_prospects.append(transformed_prospect)
            
        return {
            "status": "success",
            "message": "Prospects retrieved successfully",
            "data": transformed_prospects
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching prospects for campaign: {str(e)}"
        )

# Define the data model


def unarchive_campaign_by_id(campaign_id: str):
    try:
        campaign_users_collection = get_campaign_users_collection()
        campaign_users_collection.update_one({"_id": ObjectId(campaign_id)}, {"$set": {"isVisible": True}})
        return {
            "status": "success",
            "message": "Campaign unarchived successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

def get_archived_campaigns_list():
    try:
        campaign_users_collection = get_campaign_users_collection()
        campaigns = list(campaign_users_collection.find({"isVisible": False}))

        transformed_campaigns = [{
            "id": str(campaign["_id"]),
            "campaignName": campaign.get("campaignName"),
            "description": campaign.get("description"),
            "users": campaign.get("users"),
            "maxRetry": campaign.get("maxRetry"),
        } for campaign in campaigns]

        return transformed_campaigns
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

def get_campaign_analytics_list(campaign_id: str):
    try:
        prospects_collection = get_prospects_collection()
        
        # Base match stage for this campaign
        base_match = {"campaignId": campaign_id}
        
        # 1. Get total number of calls
        total_calls_pipeline = [
            {"$match": base_match},
            {"$unwind": {"path": "$calls", "preserveNullAndEmptyArrays": False}},
            {"$count": "totalCalls"}
        ]
        total_calls_result = next(prospects_collection.aggregate(total_calls_pipeline), {"totalCalls": 0})
        
        # 2. Get total connected calls (with status "ended")
        connected_calls_pipeline = [
            {"$match": base_match},
            {"$unwind": {"path": "$calls", "preserveNullAndEmptyArrays": False}},
            {"$match": {"calls.status": "ended"}},
            {"$count": "totalConnectedCalls"}
        ]
        connected_calls_result = next(prospects_collection.aggregate(connected_calls_pipeline), {"totalConnectedCalls": 0})
        
        # 3. Get total appointments booked
        appointments_pipeline = [
            {"$match": {**base_match, "appointment.appointmentInterest": True}},
            {"$count": "totalAppointmentsBooked"}
        ]
        appointments_result = next(prospects_collection.aggregate(appointments_pipeline), {"totalAppointmentsBooked": 0})
        
        # 4. Get total ebooks sent
        ebooks_pipeline = [
            {"$match": {**base_match, "isEbook": True}},
            {"$count": "totalEbooksSent"}
        ]
        ebooks_result = next(prospects_collection.aggregate(ebooks_pipeline), {"totalEbooksSent": 0})
        
        # 5. Get scheduled callbacks
        callbacks_pipeline = [
            {"$match": {
                **base_match, 
                "callBackDate": {"$ne": "", "$gte": datetime.now().strftime("%Y-%m-%d")}
            }},
            {"$count": "totalScheduledCallbacks"}
        ]
        callbacks_result = next(prospects_collection.aggregate(callbacks_pipeline), {"totalScheduledCallbacks": 0})


        average_call_duration_pipeline = [
            {"$match": base_match},
            {"$unwind": {"path": "$calls", "preserveNullAndEmptyArrays": False}},
            {"$group": {"_id": None, "averageCallDuration": {"$avg": "$calls.duration"}}}
        ]
        average_call_duration_result = next(prospects_collection.aggregate(average_call_duration_pipeline), {"averageCallDuration": 0})
        
        # Combine all results
        transformed_campaign = {
            "totalCalls": total_calls_result.get("totalCalls", 0),
            "totalConnectedCalls": connected_calls_result.get("totalConnectedCalls", 0),
            "totalAppointmentsBooked": appointments_result.get("totalAppointmentsBooked", 0),
            "totalEbooksSent": ebooks_result.get("totalEbooksSent", 0),
            "totalScheduledCallbacks": callbacks_result.get("totalScheduledCallbacks", 0),
            "averageCallDuration": average_call_duration_result.get("averageCallDuration", 0)
        }
        
        return {
            "status": "success",
            "message": "Campaign analytics retrieved successfully",
            "data": transformed_campaign
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving campaign analytics: {str(e)}")

class CampaignUpdate:
    campaignName: str
    campaignDate: str
    maxRetry: int
    campaignTime: str

def update_campaign_settings(campaign_id: str, campaign_update: CampaignUpdate):
    print("Campaign     :", campaign_update)
    try:
        campaign_users_collection = get_campaign_users_collection()
        prospects_collection = get_prospects_collection()
        
        # Convert the Pydantic model to a dictionary
        update_data = {
            "campaignName": campaign_update.campaignName,
            "campaignDate": campaign_update.campaignDate,
            "campaignTime": campaign_update.campaignTime,
            "maxRetry": campaign_update.maxRetry,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        print("Update data:", update_data)
        
        # Update campaign settings
        result = campaign_users_collection.update_one(
            {"_id": ObjectId(campaign_id)},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Campaign with ID {campaign_id} not found"
            )
        
        # Now update all prospects associated with this campaign
        # This will update the scheduledCallDate for all prospects with this campaignId
        if update_data.get("campaignDate"):
            prospects_update_result = prospects_collection.update_many(
                {"campaignId": campaign_id},
                {"$set": {
                    "scheduledCallDate": update_data["campaignDate"],
                    "scheduledCallTime": update_data["campaignTime"],
                    "updated_at": datetime.utcnow().isoformat()
                }}
            )
            
        return {
            "status": "success",
            "message": "Campaign settings updated successfully"
        }  
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

def get_campaign_by_id(campaign_id):
    """
    Retrieve campaign details from the campaign_users table by campaign ID
    
    Args:
        campaign_id (str): The ID of the campaign to retrieve
        
    Returns:
        dict: Campaign details if found, None otherwise
    """
    try:
        campaign_users_collection = get_campaign_users_collection()
        # Find the campaign by ID
        campaign = campaign_users_collection.find_one({"_id": campaign_id})
        # campaign = campaign_users_collection.find_one({"_id": wjer})

        return campaign
    except Exception as e:
        print(f"Error in get_campaign_by_id: {str(e)}")
        return None 
    
def delete_campaign_by_id(campaign_id: str):
    try:
        campaign_users_collection = get_campaign_users_collection()
        campaign_users_collection.update_one({"_id": ObjectId(campaign_id)}, {"$set": {"isVisible": False}})
        # campaign_users_collection.delete_one({"_id": ObjectId(campaign_id)})
        return {
            "status": "success",
            "message": "Campaign deleted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")