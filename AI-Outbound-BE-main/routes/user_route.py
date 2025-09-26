from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from services.user_service import get_users, update_user
from models.user import User
from pydantic import BaseModel
from typing import Optional

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    businessName: Optional[str] = None
    role: Optional[str] = None
    api_key: Optional[str] = None

router = APIRouter()

@router.get("/get_users")
async def get_users_route():
    try:
        users =get_users()
        print(users)
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/update_user/{user_id}")
async def update_user_route(user_id: str, user_data: UserUpdate):
    try:
        result = update_user(user_id, user_data.dict(exclude_unset=True))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
