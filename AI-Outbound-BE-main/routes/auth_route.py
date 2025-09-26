from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Annotated
from models.user import User, UserCreate, UserLogin, Token
from services.auth_service import (
    authenticate_user,
    create_user,
    get_current_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from services.campaign_service import get_brokers
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@router.post("/login", response_model=Token)
def login(form_data: UserLogin):
    user = authenticate_user(form_data.email, form_data.password)
    print("login after authenticate user", user)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/signup")
def signup(user_data: UserCreate):
    print("signup user_data", user_data)
    if user_data.password != user_data.confirmPassword:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    
    try:
        result = create_user(
            name=user_data.name,
            email=user_data.email,
            password=user_data.password,
            businessName=user_data.businessName,
            # hasEbook=user_data.hasEbook,
            # ebookPath=user_data.ebookPath
        )
        return result
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/me", response_model=User)
async def read_users_me(token: str = Depends(oauth2_scheme)):
    return get_current_user(token)

@router.post("/logout")
async def logout():
    # Since we're using JWT tokens, we don't need to do anything on the server side
    # The client should remove the token from localStorage
    return {"message": "Successfully logged out"}

@router.get("/brokers")
def get_brokers_route():
    return get_brokers() 