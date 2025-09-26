from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List

class User(BaseModel):
    # _id: Optional[str] = None
    id:  Optional[str] = Field(None, alias="_id")
    name: str
    email: EmailStr
    password: str
    role: str = "user"
    businessName: Optional[str] = None
    # hasEbook: Optional[bool] = False
    # ebookPath: Optional[str] = None
    microsoft_token: Optional[str] = None
    microsoft_refresh_token: Optional[str] = None
    microsoft_token_expires: Optional[str] = None
    microsoft_email: Optional[str] = None
    api_key: Optional[str] = None  
    # campaign_user_ids: Optional[List[str]] = []
    
    class Config:
        from_attributes = True
        allow_population_by_field_name = True

class UserNew(BaseModel):
    _id: Optional[str] = None
    name: str
    email: EmailStr
    password: str
    role: str = "user"
    businessName: Optional[str] = None
    # hasEbook: Optional[bool] = False
    # ebookPath: Optional[str] = None
    microsoft_token: Optional[str] = None
    microsoft_refresh_token: Optional[str] = None
    microsoft_token_expires: Optional[str] = None
    microsoft_email: Optional[str] = None
    api_key: Optional[str] = None  
    # campaign_user_ids: Optional[List[str]] = []
    
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    confirmPassword: str
    businessName: Optional[str] = None
    api_key: Optional[str] = None 
    # hasEbook: Optional[bool] = False
    # ebookPath: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None 