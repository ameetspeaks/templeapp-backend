from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime
import asyncio
from app.models.schemas import TempleAddRequest, TempleEnrichRequest, TempleBulkEnrichRequest, SuccessResponse, Temple, PaginationResponse
from app.services.gemini_client import GeminiClient
from app.utils.supabase_client import supabase
from app.utils.response import success_response, error_response
from app.utils.auth import verify_api_key

router = APIRouter(prefix="/v1/temples", tags=["Temples V1"])
gemini = GeminiClient()

@router.get("", response_model=SuccessResponse)
async def list_temples(
    q: Optional[str] = None,
    deity: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    api_key: str = Depends(verify_api_key)
):
    try:
        query = supabase.table("temples").select("*", count="exact")
        
        if q:
            query = query.ilike("name", f"%{q}%")
        if deity:
            query = query.eq("deity", deity)
        if city:
            query = query.eq("city", city)
        if state:
            query = query.eq("state", state)
            
        start = (page - 1) * page_size
        end = start + page_size - 1
        
        res = query.range(start, end).execute()
        
        return success_response({
            "items": res.data,
            "page": page,
            "page_size": page_size,
            "total": res.count
        })
    except Exception as e:
        return error_response(str(e), 500)

@router.get("/within-bounds", response_model=SuccessResponse)
async def temples_within_bounds(
    sw_lat: float, sw_lng: float, ne_lat: float, ne_lng: float,
    deity: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    try:
        query = supabase.table("temples").select("*")
        # Supabase (PostgREST) doesn't have native box search in simple client without GIS ext active for all columns
        # But we can use gte/lte filters on lat/lng columns if they are simple floats
        query = query.gte("latitude", sw_lat).lte("latitude", ne_lat)\
                     .gte("longitude", sw_lng).lte("longitude", ne_lng)
        
        if deity:
            query = query.eq("deity", deity)
            
        res = query.execute()
        return success_response({"items": res.data})
    except Exception as e:
        return error_response(str(e), 500)

@router.get("/{id}", response_model=SuccessResponse)
async def get_temple(id: str, api_key: str = Depends(verify_api_key)):
    try:
        res = supabase.table("temples").select("*").eq("id", id).execute()
        if not res.data:
            return error_response("Not found", 404)
        return success_response(res.data[0])
    except Exception as e:
        return error_response(str(e), 500)

@router.get("/{id}/gallery", response_model=SuccessResponse)
async def get_temple_gallery(id: str, api_key: str = Depends(verify_api_key)):
    try:
        res = supabase.table("temples").select("image_urls").eq("id", id).execute()
        if not res.data:
             return error_response("Not found", 404)
        return success_response({"images": res.data[0].get("image_urls", [])})
    except Exception as e:
        return error_response(str(e), 500)

@router.get("/{id}/timings", response_model=SuccessResponse)
async def get_temple_timings(id: str, api_key: str = Depends(verify_api_key)):
    try:
        res = supabase.table("temples").select("darshan_times, puja_times").eq("id", id).execute()
        if not res.data:
             return error_response("Not found", 404)
        return success_response(res.data[0])
    except Exception as e:
        return error_response(str(e), 500)

# --- Enrichment Endpoints (Internal/Admin) ---
@router.post("/enrich/{temple_id}", response_model=SuccessResponse)
async def enrich_temple(temple_id: str, api_key: str = Depends(verify_api_key)):
    try:
        # Fetch temple
        res = supabase.table("temples").select("*").eq("id", temple_id).execute()
        if not res.data:
            return error_response("Temple not found", 404)
        temple = res.data[0]
        
        prompt = f"""
        You are an expert Hindu temple historian. Generate info for {temple['name']}, {temple['deity']} temple in {temple['city']}, {temple['state']}.
        Output JSON: history, significance, darshan_times (list of {{label, start, end}}), puja_times (list of {{label, start, end}}), major_festivals, how_to_reach, nearby_attractions, interesting_facts, dress_code, photography_allowed, entry_fee, best_time_to_visit, image_keywords (list of strings for searching images).
        """
        
        ai_data = await gemini.generate_json(prompt, model="pro")
        
        # Transform keys to match DB if needed, or store in JSONB column 'details'
        # For now, let's map known fields
        update_data = {
            "description": ai_data.get('history', '') + "\\n\\n" + ai_data.get('significance', ''),
            "darshan_times": ai_data.get('darshan_times', []),
            "puja_times": ai_data.get('puja_times', []),
            "status": "enriched",
            # "enriched_at": datetime.now().isoformat() # Optional
        }
        
        supabase.table("temples").update(update_data).eq("id", temple_id).execute()
        return success_response(update_data, "Enriched")
    except Exception as e:
        return error_response(str(e), 500)

