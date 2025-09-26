from fastapi import APIRouter, HTTPException, Depends
from services.campaign_service import (
    create_new_campaign,
    getCampaignUsers,
    getCampaigns,
    get_campaigns_by_user_id,
    get_prospects_for_campaign,
    update_campaign_settings,
    delete_campaign_by_id,
    unarchive_campaign_by_id,
    get_archived_campaigns_list,
    get_campaign_analytics_list
)
from services.auth_service import get_current_user
from models.campaign import CampaignCreate, CampaignUpdate
from models.user import User

router = APIRouter()

@router.post("/create_campaign")
async def create_campaign(campaign: CampaignCreate):
    """
    Create a new campaign (now 1:1 with user)
    """
    try:
        result = create_new_campaign(
            campaign_name=campaign.campaignName,
            users=campaign.users,
            campaignDate=campaign.campaignDate,
            campaignTime=campaign.campaignTime,
            description=campaign.description,
            has_ebook=campaign.has_ebook
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    
@router.get("/get_campaigns")
async def get_campaigns():
    """
    Get all campaigns (each campaign is a user)
    """
    try:
        result = getCampaigns()
        return result   
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/get_campaign_users")
async def get_campaign_users():
    """
    Get all campaign users
    """
    try:
        result = getCampaignUsers()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/user_campaigns/{user_id}")
async def get_user_campaigns(user_id: str):
    """
    Get all campaigns for a specific user
    """
    try:
        print(f"Fetching campaigns for user ID: {user_id}")
        result = get_campaigns_by_user_id(user_id)
        print(f"Fetched campaigns: {result}")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/campaign_prospects/{campaign_id}")
async def get_campaign_prospects(campaign_id: str):
    """
    Get all prospects for a specific campaign
    """
    try:
        result = get_prospects_for_campaign(campaign_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.put("/update_campaign/{campaign_id}")
async def update_campaign(campaign_id: str, campaign_update: CampaignUpdate):
    """
    Update campaign settings
    """
    try:
        result = update_campaign_settings(campaign_id, campaign_update)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    

@router.get("/get_archived_campaigns")
async def get_archived_campaigns():
    """
    Get all archived campaigns
    """
    try:
        result = get_archived_campaigns_list()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/get_campaign_analytics/{campaign_id}")
async def get_campaign_analytics(campaign_id: str):
    """
    Get campaign analytics
    """
    try:
        result = get_campaign_analytics_list(campaign_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.put("/unarchive_campaign/{campaign_id}")
async def unarchive_campaign(campaign_id: str):
    """
    Unarchive a campaign
    """
    try:
        result = unarchive_campaign_by_id(campaign_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.delete("/delete_campaign/{campaign_id}")
async def delete_campaign(campaign_id: str):

    """
    Delete a campaign
    """
    try:
        result = delete_campaign_by_id(campaign_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")