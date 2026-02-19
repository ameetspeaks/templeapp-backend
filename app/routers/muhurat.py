from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from app.models.schemas import SuccessResponse, Muhurat
from app.utils.supabase_client import supabase
from app.utils.response import success_response, error_response
from app.utils.auth import verify_api_key

router = APIRouter(prefix="/v1/muhurat", tags=["Muhurat V1"])

@router.get("", response_model=SuccessResponse)
async def list_muhurats(
    type: Optional[str] = None,
    start: Optional[str] = None, # ISO date
    end: Optional[str] = None,   # ISO date
    city: str = "Delhi",
    tz: Optional[str] = "Asia/Kolkata",
    api_key: str = Depends(verify_api_key)
):
    try:
        # Default to upcoming month if no date range
        if not start:
            start = datetime.now().strftime("%Y-%m-%d")
        
        query = supabase.table("muhurats").select("*").eq("city", city).gte("date", start)
        
        if end:
            query = query.lte("date", end)
            
        if type:
            query = query.eq("type", type)
            
        res = query.order("date").execute()
        return success_response(res.data)
    except Exception as e:
        return error_response(str(e), 500)

