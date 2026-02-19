from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Optional, Dict, Any
from app.models.schemas import SuccessResponse, UserProfile
from app.utils.supabase_client import supabase
from app.utils.response import success_response, error_response
from app.utils.auth import verify_api_key

router = APIRouter(prefix="/v1", tags=["Auth & User V1"])

@router.post("/auth/login", response_model=SuccessResponse)
async def login(
    provider: str = Body(..., embed=True), # google, apple, etc.
    token: Optional[str] = Body(None, embed=True),
    api_key: str = Depends(verify_api_key)
):
    try:
        # Verify token with provider (out of scope for MVP, assuming valid from client for now or handled by Supabase Auth on client side)
        # If client uses Supabase Auth, they send access_token in Authorization header.
        # This endpoint might just return a session or user profile.
        
        # Mock response
        return success_response({
            "token": "mock-jwt-token",
            "user": {
                "id": "user_123",
                "email": "user@example.com"
            }
        })
    except Exception as e:
        return error_response(str(e), 500)

@router.post("/auth/logout", response_model=SuccessResponse)
async def logout(api_key: str = Depends(verify_api_key)):
    return success_response(None, "Logged out")

@router.get("/user/profile", response_model=SuccessResponse)
async def get_profile(api_key: str = Depends(verify_api_key)):
    try:
        # In real app, extract user_id from token
        user_id = "user_123" # Mock
        
        res = supabase.table("user_profiles").select("*").eq("id", user_id).execute()
        if not res.data:
            # Create default profile?
            return success_response({"id": user_id, "name": "Guest", "city": "Delhi"})
            
        return success_response(res.data[0])
    except Exception as e:
        return error_response(str(e), 500)

@router.put("/user/profile", response_model=SuccessResponse)
async def update_profile(
    profile: Dict[str, Any] = Body(...),
    api_key: str = Depends(verify_api_key)
):
    try:
        user_id = "user_123" # Mock
        
        # UPSERT
        data = {**profile, "id": user_id}
        res = supabase.table("user_profiles").upsert(data).execute()
        
        return success_response(res.data[0], "Profile updated")
    except Exception as e:
        return error_response(str(e), 500)
