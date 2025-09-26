from fastapi import APIRouter, Depends, HTTPException, Body, Path
from models.user import User
from models.token_model import TokenStore
from typing import Dict
import httpx
from config.database import get_database, get_users_collection
from bson import ObjectId
from datetime import datetime, timedelta, timezone
from routes.auth_route import get_current_user

router = APIRouter()
token_store = TokenStore()

@router.post("/connect/{user_id}")
async def connect_microsoft(token_data: Dict = Body(...), user_id: str = Path(...)):
    try:
        # Print the received payload
        print("Received Microsoft Connect Payload:", token_data)
        
        # Get the access token from the request
        access_token = token_data.get("accessToken")
        refresh_token = token_data.get("refreshToken")
        account = token_data.get("account")
        
        print("Access Token:", access_token[:30] + "..." if access_token else "None")
        print("Account Info:", account)
        
        # Check if we have a valid token
        if not access_token:
            return {"error": "Access token is missing"}
            
        # Store the token with expiry (default 1 hour)
        # If the token includes expiry information, extract it
        expires_in = 3600  # Default 1 hour
        if token_data.get("expiresOn"):
            # Parse the expiry date and calculate seconds until expiry
            try:
                expiry_date = datetime.fromisoformat(token_data["expiresOn"].replace("Z", "+00:00"))
                expires_in = int((expiry_date - datetime.now(timezone.utc)).total_seconds())
                print(f"Token expiry extracted: {expiry_date}, {expires_in} seconds from now")
            except Exception as e:
                print(f"Error parsing expiry date: {e}")
        
        # Store the token in the token store for backward compatibility
        token_set = token_store.set_token_with_expiry(access_token, expires_in)
        print(f"Token successfully stored: {token_set}")
        print(f"Token store now has valid token: {token_store.is_token_valid}")
        print(f"Time until expiry: {token_store.time_until_expiry} seconds")
        
        # Store the token in the user's record in the database
        users_collection = get_users_collection()
        token_expires = (datetime.now() + timedelta(seconds=expires_in)).isoformat()
        
        # Update the user's record with the Microsoft token information
        users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "microsoft_token": access_token,
                    "microsoft_refresh_token": refresh_token,
                    "microsoft_token_expires": token_expires,
                    "microsoft_email": account.get("username")
                }
            }
        )
        
        print(f"Microsoft token saved to user {user_id}")
        
        return {"message": "Successfully connected to Microsoft","user": {
            "microsoft_token": "connected",  # Don't store the actual token here for security
            "microsoft_account": account.get("username", "Unknown")
        }}
    except Exception as e:
        print("Exception in connect_microsoft:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

# Add new endpoints to manage the token
@router.get("/token/status/{user_id}")
async def get_token_status(user_id: str = None):
    """Check if we have a valid Microsoft token for the specified user"""
    try:
        if not user_id:
            return {
                "valid": False,
                "exists": False,
                "message": "User ID is required"
            }
            
        # Get user from database
        users_collection = get_users_collection()
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            return {
                "valid": False,
                "exists": False,
                "message": "User not found"
            }
        
        # Check if user has Microsoft token
        token_exists = user.get("microsoft_token") is not None
        token_valid = False
        
        # Check if token is valid (not expired)
        if token_exists and user.get("microsoft_token_expires"):
            try:
                expires_at = datetime.fromisoformat(user["microsoft_token_expires"])
                token_valid = datetime.now() < expires_at
                
                # Calculate time until expiry
                if token_valid:
                    time_until_expiry = int((expires_at - datetime.now()).total_seconds())
                else:
                    time_until_expiry = 0
            except Exception as e:
                print(f"Error parsing token expiry: {e}")
                token_valid = False
                time_until_expiry = 0
        
        response = {
            "valid": token_valid,
            "exists": token_exists,
        }
        
        # Add time information if token exists
        if token_exists and user.get("microsoft_token_expires"):
            response["expiresAt"] = user["microsoft_token_expires"]
            response["expiresIn"] = time_until_expiry
            response["isExpired"] = not token_valid
            response["microsoft_email"] = user.get("microsoft_email")
        
        return response
    except Exception as e:
        print(f"Error checking token status: {e}")
        return {
            "valid": False,
            "exists": False,
            "error": str(e)
        }

@router.post("/token/refresh/{user_id}")
async def refresh_token(token_data: Dict = Body(...), user_id: str = Path(...)):
    """Refresh the stored Microsoft token"""
    access_token = token_data.get("accessToken")
    refresh_token = token_data.get("refreshToken")
    if not access_token:
        raise HTTPException(status_code=400, detail="Access token is required")
    
    # Parse JWT token to extract expiry if not provided
    expires_in = token_data.get("expiresIn")
    if not expires_in:
        try:
            # Try to extract expiry from token
            token_parts = access_token.split('.')
            if len(token_parts) > 1:
                import base64
                import json
                
                # Fix padding for base64 decoding
                padded = token_parts[1] + '=' * (4 - len(token_parts[1]) % 4)
                
                # Decode payload
                decoded = base64.b64decode(padded)
                payload = json.loads(decoded)
                
                if 'exp' in payload:
                    exp_timestamp = payload['exp']
                    current_timestamp = datetime.now().timestamp()
                    expires_in = max(0, int(exp_timestamp - current_timestamp))
                    print(f"Extracted token expiry: {expires_in} seconds from now")
        except Exception as e:
            print(f"Error extracting token expiry: {e}")
            expires_in = 3600  # Default to 1 hour
    
    # Store in token store for backward compatibility
    token_set = token_store.set_token_with_expiry(access_token, expires_in or 3600)
    print(f"Token refreshed successfully: {token_set}")
    print(f"Token validity: {token_store.is_token_valid}")
    print(f"Time until expiry: {token_store.time_until_expiry} seconds")
    
    # Store the token in the user's record in the database
    users_collection = get_users_collection()
    token_expires = (datetime.now() + timedelta(seconds=expires_in or 3600)).isoformat()
    
    # Update the user's record with the Microsoft token information
    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "microsoft_token": access_token,
                "microsoft_refresh_token": refresh_token,
                "microsoft_token_expires": token_expires
            }
        }
    )
    
    print(f"Microsoft token refreshed and saved to user {user_id}")
    
    return {
        "message": "Token refreshed successfully",
        "valid": token_store.is_token_valid,
        "expiresIn": token_store.time_until_expiry
    }

@router.post("/token/clear")
async def clear_token():
    """Clear the stored Microsoft token"""
    token_store.clear_token()
    return {"message": "Token cleared successfully"}

# Create a new endpoint to use the stored token for graph API calls
@router.post("/graph-api/{endpoint:path}")
async def call_graph_api(endpoint: str, data: Dict = Body(None)):
    """
    Call Microsoft Graph API using the stored token
    Example: POST /api/auth/microsoft/graph-api/me/calendar/events
    """
    if not token_store.is_token_valid:
        raise HTTPException(status_code=401, detail="No valid Microsoft token available")
    
    try:
        method = data.get("method", "GET") if data else "GET"
        body = data.get("body") if data else None
        
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {token_store.microsoft_token}",
                "Content-Type": "application/json"
            }
            
            url = f"https://graph.microsoft.com/v1.0/{endpoint}"
            
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                response = await client.post(url, json=body, headers=headers)
            elif method == "PATCH":
                response = await client.patch(url, json=body, headers=headers)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported method: {method}")
            
            if response.status_code >= 200 and response.status_code < 300:
                try:
                    return response.json()
                except:
                    return {"raw_response": response.text}
            else:
                return {"error": f"Graph API request failed. Status: {response.status_code}", "details": response.text}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))