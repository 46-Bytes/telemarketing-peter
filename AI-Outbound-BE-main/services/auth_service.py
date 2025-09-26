from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status
from models.user import User, UserNew
from config.database import get_users_collection
import os
from dotenv import load_dotenv
import logging
import bcrypt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
BENCHMARK_API_KEY = os.getenv("BENCHMARK_API_KEY")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    try:
        encoded_jwt = jwt.encode(
            to_encode,
            SECRET_KEY.encode('utf-8'),  # Convert to bytes
            algorithm=ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating JWT token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating access token"
        )

def authenticate_user(email: str, password: str) -> Optional[UserNew]:
    try:
        users = get_users_collection()
        user = users.find_one({"email": email})
        if not user:
            return None
        if not verify_password(password, user["password"]):
            return None
    
        return UserNew(**user)
    except Exception as e:
        logger.error(f"Error in authenticate_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )

def get_current_user(token: str) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY.encode('utf-8'),
            algorithms=[ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    try:
        users = get_users_collection()
        user = users.find_one({"email": email})
        if user is None:
            raise credentials_exception
        # Convert _id to string
        user["_id"] = str(user["_id"])
        user["userId"] = str(user["_id"])   
        return user
    except Exception as e:
        logger.error(f"Error in get_current_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user: {str(e)}"
        )

def create_user(name: str, email: str, password: str, businessName: str = None):
    try:
        users = get_users_collection()
        from config.database import get_campaigns_collection
        # Check if user already exists
        existing_user = users.find_one({"email": email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = get_password_hash(password)
       
        result = users.insert_one({
            "name": name,
            "email": email,
            "password": hashed_password,
            "role": "user",  # Default role
            "businessName": businessName,
            "api_key": BENCHMARK_API_KEY
            # "hasEbook": hasEbook,
            # "ebookPath": ebookPath,
            # "campaign_user_ids": []  # Initialize as empty array
        })

        user_id = str(result.inserted_id)

        # # Create a campaign for this user
        # campaign_collection = get_campaigns_collection()
        # campaign_collection.insert_one({
        #     "campaignName": name,  # Full name as campaign name
        #     "owner_id": user_id,
        #     "users": [],
        #     "businessName": businessName,
        #     "fullname": name,
        #     "email": email,
        #     "created_at": datetime.utcnow().isoformat(),
        #     "updated_at": datetime.utcnow().isoformat()
        # })

        return {
            "message": "User created successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in create_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )

def get_user_from_token(token: str) -> UserNew:
    """
    Get user from a raw JWT token (without Bearer prefix)
    """
    logger.info("Authenticating user from token")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY.encode('utf-8'),
            algorithms=[ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            logger.error("Token payload missing email")
            raise credentials_exception
            
        logger.info(f"Token decoded, email: {email}")
    except JWTError as e:
        logger.error(f"JWT error: {str(e)}")
        raise credentials_exception
        
    try:
        users = get_users_collection()
        user = users.find_one({"email": email})
        if user is None:
            logger.error(f"User not found: {email}")
            raise credentials_exception
            
        logger.info(f"User found: {user['name']}")
        return UserNew(**user)
    except Exception as e:
        logger.error(f"Error in get_user_from_token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user: {str(e)}"
        )
    