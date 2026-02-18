from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import datetime
from app.models.schemas import SuccessResponse
from app.utils.supabase_client import supabase
from app.utils.response import success_response, error_response
from app.utils.auth import verify_api_key
from app.utils.supabase_client import supabase
from app.utils.response import success_response, error_response
from app.utils.auth import verify_api_key

router = APIRouter(prefix="/panchang", tags=["Panchang"])

@router.get("/list", response_model=SuccessResponse)
async def list_panchang(month: int, year: int, city: str = "Delhi", api_key: str = Depends(verify_api_key)):
    try:
        # Construct start and end dates
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{month+1:02d}-01"
            
        res = supabase.table("panchang_daily").select("*").eq("city", city).gte("date", start_date).lt("date", end_date).execute()
        return success_response(res.data)
    except Exception as e:
        return error_response(str(e), 500)

@router.get("/{date}", response_model=SuccessResponse)
async def get_panchang(date: str, city: str = "Delhi", api_key: str = Depends(verify_api_key)):
    try:
        res = supabase.table("panchang_daily").select("*").eq("date", date).eq("city", city).execute()
        if not res.data:
            return error_response("Panchang not found", 404)
        return success_response(res.data[0])
    except Exception as e:
        return error_response(str(e), 500)

@router.delete("/{date}", response_model=SuccessResponse)
async def delete_panchang(date: str, city: str = "Delhi", api_key: str = Depends(verify_api_key)):
    try:
        supabase.table("panchang_daily").delete().eq("date", date).eq("city", city).execute()
        return success_response(None, "Deleted successfully")
    except Exception as e:
        return error_response(str(e), 500)
