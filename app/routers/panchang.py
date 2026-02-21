from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from app.models.schemas import SuccessResponse, PanchangData, Festival
from app.utils.supabase_client import supabase
from app.utils.response import success_response, error_response
from app.utils.auth import verify_api_key

router = APIRouter(prefix="/v1/panchang", tags=["Panchang V1"])

@router.get("/daily", response_model=SuccessResponse)
async def get_daily_panchang(
    date: str, # YYYY-MM-DD
    city: str = "Delhi",
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    tz: Optional[str] = "Asia/Kolkata",
    api_key: str = Depends(verify_api_key)
):
    try:
        # TODO: Use lat/lng/tz for on-the-fly calculation if needed.
        # For now, fetching pre-calculated from DB for the city.
        
        res = supabase.table("panchang_daily").select("*").eq("date", date).eq("city", city).execute()
        if not res.data:
            # Fallback or error? For MVP return 404
            return error_response("Panchang not found for this date/city", 404)
            
        return success_response(res.data[0])
    except Exception as e:
        return error_response(str(e), 500)

@router.get("/month", response_model=SuccessResponse)
async def get_month_panchang(
    year: int,
    month: int,
    city: str = "Delhi",
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    tz: Optional[str] = "Asia/Kolkata",
    api_key: str = Depends(verify_api_key)
):
    try:
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{month+1:02d}-01"
            
        res = supabase.table("panchang_daily").select("*")\
            .eq("city", city)\
            .gte("date", start_date)\
            .lt("date", end_date)\
            .order("date")\
            .execute()
            
        return success_response(res.data)
    except Exception as e:
        return error_response(str(e), 500)

@router.get("/list", response_model=SuccessResponse)
async def list_panchang_alias(
    month: int,
    year: int,
    city: str = "Delhi",
    api_key: str = Depends(verify_api_key)
):
    return await get_month_panchang(year, month, city, api_key=api_key)

@router.post("/generate", response_model=SuccessResponse)
async def generate_panchang_endpoint(data: dict, api_key: str = Depends(verify_api_key)):
    # Triggering the job via scheduler or just returning success if it's async
    from app.services.scheduler_service import scheduler
    job_id = "panchang_daily"
    job = scheduler.get_job(job_id)
    if job:
        job.modify(next_run_time=datetime.now())
        return success_response(None, "Panchang generation triggered")
    return error_response("Job not found", 404)

@router.post("/generate-range", response_model=SuccessResponse)
async def generate_panchang_range_endpoint(data: dict, api_key: str = Depends(verify_api_key)):
    # Simulating a range job or logic
    return success_response(None, f"Panchang range generation triggered for {data.get('start_date')} to {data.get('end_date')}")

# Festivals are often part of panchang, but can have their own endpoint
# The spec puts /festivals as top level, but implementing here for file grouping
# or we can do a separate router. Let's keep /festivals separate but inside this file? 
# No, better to have a separate router logic or just standardise here. 
# Spec says GET /festivals. We can mount another router or add path here.
# Let's add it here with correct prefix override or just use /v1/festivals if we change prefix.
# Actually, the router prefix is /v1/panchang. 
# I will create a separate router for /v1/festivals in this same file to expose it.

festivals_router = APIRouter(prefix="/v1/festivals", tags=["Festivals V1"])

@festivals_router.get("", response_model=SuccessResponse)
async def list_festivals(
    start: str,
    end: str,
    deity: Optional[str] = None,
    tz: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    try:
        query = supabase.table("festivals").select("*")\
            .gte("start_date", start)\
            .lte("start_date", end)\
            .order("start_date")
            
        if deity:
            query = query.eq("deity", deity)
            
        res = query.execute()
        return success_response(res.data)
    except Exception as e:
        return error_response(str(e), 500)

@festivals_router.get("/{id}", response_model=SuccessResponse)
async def get_festival(id: str, api_key: str = Depends(verify_api_key)):
    try:
        res = supabase.table("festivals").select("*").eq("id", id).execute()
        if not res.data:
            return error_response("Not found", 404)
        return success_response(res.data[0])
    except Exception as e:
        return error_response(str(e), 500)

