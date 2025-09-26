# Pydantic models for data validation

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Union

class ProspectIn(BaseModel):
    name: str
    phoneNumber: str
    businessName: str = ""
    email: str = ""
    scheduledCallDate: Optional[Union[datetime, str]] = None  
    ownerName: Optional[str] = None  
    campaignId: Optional[str] = None
    campaignName: Optional[str] = None  # Keep for backward compatibility  
    scheduledCallTime: Optional[str] = None