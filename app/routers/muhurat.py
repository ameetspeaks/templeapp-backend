from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta
from datetime import datetime, timedelta
from app.models.schemas import SuccessResponse
from app.utils.supabase_client import supabase
from app.utils.response import success_response, error_response
from app.utils.auth import verify_api_key
from app.utils.supabase_client import supabase
from app.utils.response import success_response, error_response
from app.utils.auth import verify_api_key

router = APIRouter(prefix="/muhurat", tags=["Muhurat"])

@router.get("/upcoming", response_model=SuccessResponse)
async def upcoming_muhurats(type: str, days: int = 30, city: str = "Delhi", api_key: str = Depends(verify_api_key)):
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        end = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        res = supabase.table("muhurats").select("*").eq("type", type).eq("city", city).gte("date", today).lte("date", end).order("date").execute()
        return success_response(res.data)
    except Exception as e:
        return error_response(str(e), 500)

@router.get("/list", response_model=SuccessResponse)
async def list_muhurats(type: str, month: int, year: int, api_key: str = Depends(verify_api_key)):
    try:
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{month+1:02d}-01"
            
        res = supabase.table("muhurats").select("*").eq("type", type).gte("date", start_date).lt("date", end_date).execute()
        return success_response(res.data)
    except Exception as e:
        return error_response(str(e), 500)
