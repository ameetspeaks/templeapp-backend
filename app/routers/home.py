from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from app.models.schemas import SuccessResponse, HomeSummary, PanchangData, Festival
from app.utils.supabase_client import supabase
from app.utils.response import success_response, error_response
from app.utils.auth import verify_api_key

router = APIRouter(prefix="/v1/home", tags=["Home V1"])

@router.get("/summary", response_model=SuccessResponse)
async def get_home_summary(
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    tz: Optional[str] = "Asia/Kolkata",
    date: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    try:
        today = date or datetime.now().strftime("%Y-%m-%d")
        city = "Delhi" # Default or reverse geocode if lat/lng provided (omitted for MVP)
        
        # 1. Fetch Panchang
        panchang_res = supabase.table("panchang_daily").select("*").eq("date", today).eq("city", city).execute()
        panchang = panchang_res.data[0] if panchang_res.data else {
            "date": today,
            "city": city,
            "tithi": "Unknown",
            "nakshatra": "Unknown",
            "sunrise": "06:00",
            "sunset": "18:00",
            "yoga": "Unknown",
            "karan": "Unknown",
            "rahukaal": "Unknown",
            "paksha": "Unknown"
        }
        
        # 2. Fetch Featured Festivals (upcoming 7 days)
        # TODO: Define "Featured" logic. For now, next few festivals.
        festivals_res = supabase.table("festivals").select("*")\
            .gte("start_date", today)\
            .limit(3)\
            .order("start_date")\
            .execute()
            
        # 3. Quick Counts
        # Nearby temples (mock logic without PostGIS or complex query for MVP)
        # Just creating a placeholder or simple count
        temple_count_res = supabase.table("temples").select("*", count="exact", head=True).execute()
        muhurat_count_res = supabase.table("muhurats").select("*", count="exact", head=True)\
            .eq("city", city).gte("date", today).execute()
            
        return success_response({
            "greeting": "Good Morning" if datetime.now().hour < 12 else "Good Evening", # Simple logic
            "panchang": panchang,
            "featured_festivals": festivals_res.data,
            "quick_counts": {
                "nearby_temples": temple_count_res.count, # This is total, not nearby. Good enough for MVP.
                "today_muhurat": muhurat_count_res.count
            }
        })
    except Exception as e:
        return error_response(str(e), 500)
