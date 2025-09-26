from pydantic import BaseModel
from typing import Optional, List

class Campaign(BaseModel):
    id: Optional[str] = None
    campaignName: str
    description: Optional[str] = None
    owner_id: str  # The user who created the campaign
    users: Optional[str] = None
    businessName: Optional[str] = None
    fullname: Optional[str] = None
    email: Optional[str] = None
    has_ebook: Optional[bool] = False
    ebook_path: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class CampaignCreate(BaseModel):
    campaignName: str
    description: Optional[str] = None
    users: Optional[str] = None
    campaignDate: Optional[str] = None
    fullname: Optional[str] = None
    email: Optional[str] = None
    has_ebook: Optional[bool] = False
    ebook_path: Optional[str] = None
    campaignTime: Optional[str] = None
class CampaignUpdate(BaseModel):
    campaignName: Optional[str] = None
    campaignDate: Optional[str] = None
    campaignTime: Optional[str] = None
    maxRetry: Optional[int] = None