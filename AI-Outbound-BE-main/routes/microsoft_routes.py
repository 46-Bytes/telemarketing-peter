from fastapi import APIRouter, Depends, HTTPException, Body, Request
from typing import Dict, Any, Optional
from services.microsoft_service import (
    connect_microsoft_account,
    refresh_microsoft_token,
    check_token_status,
    call_graph_api_for_user,
    create_calendar_event,
    initiate_oauth_flow,
    complete_oauth_flow,
    disconnect_microsoft_account
)

router = APIRouter(
    prefix="/api/auth/microsoft",
    tags=["microsoft"],
    responses={404: {"description": "Not found"}},
)

@router.get("/login/{user_id}")
async def login(user_id: str):
    """Initiate Microsoft OAuth flow"""
    return initiate_oauth_flow(user_id)

@router.get("/callback")
async def callback(code: str, state: str, request: Request):
    """Handle OAuth callback"""
    return await complete_oauth_flow(code, state, request)

@router.post("/connect/{user_id}")
async def connect_account(
    user_id: str,
    data: Dict[str, Any] = Body(...)
):
    """Connect a Microsoft account to a user using authorization code"""
    code = data.get("code")
    
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code is required")
    
    return await complete_oauth_flow(code, user_id, None)

@router.post("/token/refresh/{user_id}")
async def refresh_token(
    user_id: str,
    data: Dict[str, Any] = Body(...)
):
    """Refresh Microsoft access token"""
    access_token = data.get("accessToken")
    expires_in = data.get("expiresIn")
    
    if not access_token:
        raise HTTPException(status_code=400, detail="Access token is required")
    
    return refresh_microsoft_token(user_id, access_token, expires_in)

@router.get("/token/status/{user_id}")
async def token_status(user_id: str):
    """Check the status of a Microsoft token"""
    return check_token_status(user_id)

@router.post("/graph-api/{endpoint:path}")
async def call_graph_api(
    endpoint: str,
    user_id: str = Body(...),
    method: str = Body("GET"),
    body: Optional[Dict[str, Any]] = Body(None)
):
    """Call Microsoft Graph API on behalf of a user"""
    return call_graph_api_for_user(user_id, endpoint, method, body)

@router.post("/calendar/event")
async def create_event(
    user_id: str = Body(...),
    event_details: Dict[str, Any] = Body(...)
):
    """Create a calendar event for a user"""
    return create_calendar_event(user_id, event_details)

@router.post("/disconnect/{user_id}")
async def disconnect_account(user_id: str):
    """Disconnect a Microsoft account"""
    return disconnect_microsoft_account(user_id) 