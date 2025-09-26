from fastapi import HTTPException, Request
import requests
from datetime import datetime, timedelta
import json
import secrets
import urllib.parse
import hashlib
import base64
from bson import ObjectId
from config.database import get_users_collection
import os
from typing import Dict, Any, Optional

# Microsoft OAuth configuration
CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")
TENANT_ID = os.getenv("MICROSOFT_TENANT_ID")
REDIRECT_URI = os.getenv("MICROSOFT_REDIRECT_URI")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
TOKEN_ENDPOINT = f"{AUTHORITY}/oauth2/v2.0/token"
AUTH_ENDPOINT = f"{AUTHORITY}/oauth2/v2.0/authorize"
GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"

# Scopes required for Microsoft Graph API
DEFAULT_SCOPES = ["User.Read", "Calendars.ReadWrite", "Mail.Send", "offline_access", "openid", "profile", "Calendars.Read"]

def get_microsoft_data(user_id: str) -> Dict:
    """Get Microsoft authentication data for a user"""
    try:
        users_collection = get_users_collection()
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        microsoft_data = user.get("microsoft_auth", {})
        return microsoft_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving Microsoft data: {str(e)}")

def update_microsoft_data(user_id: str, microsoft_data: Dict) -> None:
    """Update Microsoft authentication data for a user"""
    try:
        users_collection = get_users_collection()
        users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"microsoft_auth": microsoft_data}}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating Microsoft data: {str(e)}")

def generate_code_verifier() -> str:
    """Generate a code verifier for PKCE"""
    return secrets.token_urlsafe(64)[:128]

def generate_code_challenge(code_verifier: str) -> str:
    """Generate a code challenge from the code verifier using S256 method"""
    code_challenge_digest = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge_digest).decode('utf-8')
    return code_challenge.rstrip('=')  # Remove padding characters

def initiate_oauth_flow(user_id: str) -> Dict:
    """Initiate Microsoft OAuth flow with PKCE"""
    try:
        # Generate a state parameter to prevent CSRF
        state = f"{user_id}:{secrets.token_urlsafe(16)}"
        
        # Generate PKCE code verifier and challenge
        code_verifier = generate_code_verifier()
        code_challenge = generate_code_challenge(code_verifier)
        print("codeChallenge", code_challenge)
        
        # Store the state and code verifier in the user's record for verification
        microsoft_data = get_microsoft_data(user_id)
        microsoft_data["oauth_state"] = state
        microsoft_data["code_verifier"] = code_verifier
        update_microsoft_data(user_id, microsoft_data)
        
        print("codeVerifier", code_verifier)
        # Construct the authorization URL with PKCE
        scopes = " ".join(DEFAULT_SCOPES)
        params = {
            "client_id": CLIENT_ID,
            "response_type": "code",
            "redirect_uri": REDIRECT_URI,
            "response_mode": "query",
            "scope": scopes,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }
        
        auth_url = f"{AUTH_ENDPOINT}?{urllib.parse.urlencode(params)}"
        
        return {
            "authUrl": auth_url,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initiating OAuth flow: {str(e)}")

async def complete_oauth_flow(code: str, state: str, request: Optional[Request] = None) -> Dict:
    """Complete Microsoft OAuth flow with PKCE"""
    try:
        print(f"state: {state}")
        print("code", code)
        # Extract user_id from state
        if ":" in state:
            user_id, _ = state.split(":", 1)
        else:
            user_id = state  # For direct API calls where state is just the user_id
        
        # Get the user's Microsoft data
        microsoft_data = get_microsoft_data(user_id)
        print("microsoft_data", microsoft_data)
        
        # Validate state if this is a callback from Microsoft
        if request is not None:
            stored_state = microsoft_data.get("oauth_state")
            
            if not stored_state or stored_state != state:
                # Invalid state, potential CSRF attack
                raise HTTPException(status_code=400, detail="Invalid state parameter")
        
        # Get the code verifier
        code_verifier = microsoft_data.get("code_verifier")
        print("codeVerifier", code_verifier)
        if not code_verifier:
            raise HTTPException(status_code=400, detail="Code verifier not found")
        
        # Exchange the authorization code for tokens with PKCE
        token_data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
            "code_verifier": code_verifier
        }
        
        token_response = requests.post(TOKEN_ENDPOINT, data=token_data)

        print("token_response", token_response)
        
        if token_response.status_code != 200:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to exchange authorization code: {token_response.text}"
            )
        
        tokens = token_response.json()

        print("tokens", tokens)
        
        # Get user profile from Microsoft Graph
        access_token = tokens["access_token"]
        user_profile = call_microsoft_graph("me", access_token)

        print("access_token", access_token)
        
        # Calculate token expiry times
        now = datetime.now()
        token_expiry = (now + timedelta(seconds=tokens["expires_in"])).isoformat()
        
        # Calculate refresh token expiry (default to 14 days if not provided)
        refresh_token_expiry = None
        if "refresh_token_expires_in" in tokens:
            refresh_token_expiry = (now + timedelta(seconds=tokens["refresh_token_expires_in"])).isoformat()
        else:
            refresh_token_expiry = (now + timedelta(days=14)).isoformat()
        
        # Store Microsoft account information
        microsoft_data = {
            "access_token": access_token,
            "refresh_token": tokens["refresh_token"],
            "id_token": tokens.get("id_token"),
            "user_profile": user_profile,
            "token_expiry": token_expiry,
            "refresh_token_expiry": refresh_token_expiry,
            "connected_at": now.isoformat()
        }
        
        # Update user record with Microsoft data
        update_microsoft_data(user_id, microsoft_data)
        
        # If this is a callback from Microsoft, return HTML that sends a message to the opener
        if request is not None:
            return {
                "status": "success",
                "message": "Microsoft account connected successfully",
                "data": {
                    "user_profile": user_profile
                }
            }
        # Otherwise, return JSON response for API calls
        return {
            "status": "success",
            "message": "Microsoft account connected successfully",
            "data": {
                "user_profile": user_profile,
                "expiresIn": calculate_seconds_until(token_expiry),
                "refresh_token_expires_in": calculate_seconds_until(refresh_token_expiry)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error completing OAuth flow: {str(e)}")

def connect_microsoft_account(user_id: str, access_token: str, account_info: Dict, expires_on: Optional[str] = None) -> Dict:
    """Connect a Microsoft account to a user (legacy method, use complete_oauth_flow instead)"""
    try:
        # Validate the access token by making a call to Microsoft Graph
        user_profile = call_microsoft_graph("me", access_token)
        
        # Extract token expiry information
        token_expiry = None
        refresh_token_expiry = None
        
        if expires_on:
            token_expiry = expires_on
        else:
            # Default to 1 hour from now if not provided
            token_expiry = (datetime.now() + timedelta(hours=1)).isoformat()
        
        # Default refresh token expiry (24 hours)
        refresh_token_expiry = (datetime.now() + timedelta(hours=24)).isoformat()
        
        # Store Microsoft account information
        microsoft_data = {
            "access_token": access_token,
            "account_info": account_info,
            "user_profile": user_profile,
            "token_expiry": token_expiry,
            "refresh_token_expiry": refresh_token_expiry,
            "connected_at": datetime.now().isoformat()
        }
        
        # Update user record with Microsoft data
        update_microsoft_data(user_id, microsoft_data)
        
        return {
            "status": "success",
            "message": "Microsoft account connected successfully",
            "data": {
                "user_profile": user_profile,
                "expiresIn": calculate_seconds_until(token_expiry),
                "refresh_token_expires_in": calculate_seconds_until(refresh_token_expiry)
            }
        }
    except Exception as e:
        if "token is expired" in str(e).lower():
            return {
                "status": "error",
                "error": "token is expired",
                "message": "Microsoft token is expired. Please refresh and try again."
            }
        raise HTTPException(status_code=500, detail=f"Error connecting Microsoft account: {str(e)}")

def refresh_microsoft_token(user_id: str, access_token: str = None, expires_in: Optional[int] = None) -> Dict:
    """Refresh Microsoft access token"""
    try:
        # Get current Microsoft data
        microsoft_data = get_microsoft_data(user_id)
        
        if not microsoft_data:
            raise HTTPException(status_code=404, detail="No Microsoft account connected")
        
        # If we have a refresh token, use it to get a new access token
        refresh_token = microsoft_data.get("refresh_token")
        
        if refresh_token:
            # Use refresh token to get new access token
            token_data = {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            }
            
            token_response = requests.post(TOKEN_ENDPOINT, data=token_data)
            
            if token_response.status_code != 200:
                # If refresh token is invalid, we need to reconnect
                raise HTTPException(
                    status_code=401, 
                    detail="Refresh token is invalid or expired. Please reconnect your Microsoft account."
                )
            
            tokens = token_response.json()
            
            # Update tokens in database
            microsoft_data["access_token"] = tokens["access_token"]
            
            # Update refresh token if provided
            if "refresh_token" in tokens:
                microsoft_data["refresh_token"] = tokens["refresh_token"]
            
            # Calculate token expiry times
            now = datetime.now()
            token_expiry = (now + timedelta(seconds=tokens["expires_in"])).isoformat()
            microsoft_data["token_expiry"] = token_expiry
            
            # Calculate refresh token expiry if provided
            if "refresh_token_expires_in" in tokens:
                refresh_token_expiry = (now + timedelta(seconds=tokens["refresh_token_expires_in"])).isoformat()
                microsoft_data["refresh_token_expiry"] = refresh_token_expiry
            
            # Update user record with new token data
            update_microsoft_data(user_id, microsoft_data)
            
            return {
                "status": "success",
                "message": "Microsoft token refreshed successfully",
                "valid": True,
                "expiresIn": calculate_seconds_until(token_expiry),
                "refresh_token_expires_in": calculate_seconds_until(microsoft_data.get("refresh_token_expiry"))
            }
        elif access_token:
            # Legacy method: Update with provided access token
            microsoft_data["access_token"] = access_token
            
            # Calculate new expiry time
            if expires_in:
                token_expiry = (datetime.now() + timedelta(seconds=expires_in)).isoformat()
            else:
                # Default to 1 hour from now
                token_expiry = (datetime.now() + timedelta(hours=1)).isoformat()
                
            microsoft_data["token_expiry"] = token_expiry
            
            # Update user record with new token data
            update_microsoft_data(user_id, microsoft_data)
            
            return {
                "status": "success",
                "message": "Microsoft token updated successfully",
                "valid": True,
                "expiresIn": calculate_seconds_until(token_expiry)
            }
        else:
            raise HTTPException(status_code=400, detail="No refresh token or access token available")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refreshing Microsoft token: {str(e)}")

def check_token_status(user_id: str) -> Dict:
    """Check the status of a Microsoft token"""
    try:
        # Get Microsoft data for the user
        microsoft_data = get_microsoft_data(user_id)
        
        if not microsoft_data or "access_token" not in microsoft_data:
            return {
                "valid": False,
                "exists": False,
                "message": "No Microsoft account connected"
            }
        
        # Check if token is expired
        token_expiry = microsoft_data.get("token_expiry")
        refresh_token_expiry = microsoft_data.get("refresh_token_expiry")
        
        now = datetime.now().isoformat()
        is_expired = token_expiry and token_expiry < now
        is_refresh_expired = refresh_token_expiry and refresh_token_expiry < now
        
        # If access token is expired but refresh token is valid, try to refresh
        if is_expired and not is_refresh_expired and "refresh_token" in microsoft_data:
            try:
                refresh_result = refresh_microsoft_token(user_id)
                if refresh_result["valid"]:
                    return {
                        "valid": True,
                        "exists": True,
                        "isExpired": False,
                        "expiresIn": refresh_result["expiresIn"],
                        "refresh_token_expires_in": refresh_result.get("refresh_token_expires_in")
                    }
            except Exception as e:
                print(f"Error auto-refreshing token: {e}")
                # Continue with normal status check
        
        # Calculate seconds until expiry
        expires_in = calculate_seconds_until(token_expiry) if token_expiry else 0
        refresh_token_expires_in = calculate_seconds_until(refresh_token_expiry) if refresh_token_expiry else 0
        
        return {
            "valid": not is_expired,
            "exists": True,
            "isExpired": is_expired,
            "isRefreshExpired": is_refresh_expired,
            "expiresIn": expires_in,
            "expiresAt": token_expiry,
            "refresh_token_expires_in": refresh_token_expires_in
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking token status: {str(e)}")

def call_microsoft_graph(endpoint: str, access_token: str, method: str = "GET", data: Any = None) -> Dict:
    """Call Microsoft Graph API with the provided access token"""
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        url = f"{GRAPH_BASE_URL}/{endpoint}"
        
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "PATCH":
            response = requests.patch(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported method: {method}")
        
        # Check for errors
        if response.status_code >= 400:
            error_data = response.json()
            error_message = error_data.get("error", {}).get("message", "Unknown error")
            
            if response.status_code == 401:
                raise HTTPException(status_code=401, detail=f"Microsoft token is expired or invalid: {error_message}")
            
            raise HTTPException(status_code=response.status_code, detail=f"Microsoft Graph API error: {error_message}")
        
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error calling Microsoft Graph API: {str(e)}")

def call_graph_api_for_user(user_id: str, endpoint: str, method: str = "GET", data: Any = None) -> Dict:
    """Call Microsoft Graph API on behalf of a user"""
    try:
        # Get Microsoft data for the user
        microsoft_data = get_microsoft_data(user_id)
        
        if not microsoft_data or "access_token" not in microsoft_data:
            raise HTTPException(status_code=404, detail="No Microsoft account connected")
        
        # Check if token is expired
        token_status = check_token_status(user_id)
        if token_status["isExpired"]:
            # Try to refresh the token
            if "refresh_token" in microsoft_data and not token_status.get("isRefreshExpired", True):
                refresh_result = refresh_microsoft_token(user_id)
                if not refresh_result["valid"]:
                    raise HTTPException(status_code=401, detail="Failed to refresh Microsoft token. Please reconnect your account.")
                
                # Get updated Microsoft data
                microsoft_data = get_microsoft_data(user_id)
            else:
                raise HTTPException(status_code=401, detail="Microsoft token is expired. Please reconnect your account.")
        
        access_token = microsoft_data["access_token"]
        
        # Call Microsoft Graph API
        return call_microsoft_graph(endpoint, access_token, method, data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling Microsoft Graph API: {str(e)}")

def create_calendar_event(user_id: str, event_details: Dict) -> Dict:
    """Create a calendar event for a user"""
    return call_graph_api_for_user(user_id, "me/calendar/events", "POST", event_details)

def disconnect_microsoft_account(user_id: str) -> Dict:
    """Disconnect a Microsoft account"""
    try:
        # Remove Microsoft data from user record
        users_collection = get_users_collection()
        users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$unset": {"microsoft_auth": ""}}
        )
        
        return {
            "status": "success",
            "message": "Microsoft account disconnected successfully",
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error disconnecting Microsoft account: {str(e)}")

def calculate_seconds_until(iso_datetime: Optional[str]) -> int:
    """Calculate seconds until the given ISO datetime"""
    if not iso_datetime:
        return 0
        
    try:
        expiry_time = datetime.fromisoformat(iso_datetime)
        now = datetime.now()
        
        if expiry_time < now:
            return 0
            
        delta = expiry_time - now
        return int(delta.total_seconds())
    except Exception:
        return 0 