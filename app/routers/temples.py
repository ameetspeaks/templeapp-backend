from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import math
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
        query = query.gte("latitude", sw_lat).lte("latitude", ne_lat)\
                     .gte("longitude", sw_lng).lte("longitude", ne_lng)
        
        if deity:
            query = query.eq("deity", deity)
            
        res = query.execute()
        return success_response({"items": res.data})
    except Exception as e:
        return error_response(str(e), 500)

@router.get("/nearby", response_model=SuccessResponse)
async def get_nearby_temples(
    lat: float,
    lng: float,
    radius: float = 10.0, # km
    page: int = 1,
    page_size: int = 10,
    api_key: str = Depends(verify_api_key)
):
    try:
        # Bounding box calculation for efficiency
        # 1 degree of lat ~ 111km
        lat_delta = radius / 111.0
        # 1 degree of lng ~ 111km * cos(lat)
        lng_delta = radius / (111.0 * math.cos(math.radians(lat)))
        
        sw_lat, sw_lng = lat - lat_delta, lng - lng_delta
        ne_lat, ne_lng = lat + lat_delta, lng + lng_delta
        
        # Query within bounding box first
        query = supabase.table("temples").select("*", count="exact")
        query = query.gte("latitude", sw_lat).lte("latitude", ne_lat)\
                     .gte("longitude", sw_lng).lte("longitude", ne_lng)
        
        res = query.execute()
        
        # Calculate real distances and sort
        temples = []
        for t in res.data:
            t_lat = float(t.get('latitude', 0))
            t_lng = float(t.get('longitude', 0))
            
            # Haversine formula
            R = 6371.0 # Earth radius in km
            d_lat = math.radians(t_lat - lat)
            d_lng = math.radians(t_lng - lng)
            a = math.sin(d_lat / 2)**2 + math.cos(math.radians(lat)) * math.cos(math.radians(t_lat)) * math.sin(d_lng / 2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            dist = R * c
            
            if dist <= radius:
                t['distance_km'] = round(dist, 2)
                temples.append(t)
        
        # Sort by distance
        temples.sort(key=lambda x: x['distance_km'])
        
        # Pagination
        start = (page - 1) * page_size
        end = start + page_size
        paginated_items = temples[start:end]
        
        return success_response({
            "items": paginated_items,
            "page": page,
            "page_size": page_size,
            "total": len(temples)
        })
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

@router.post("/{id}/favorite", response_model=SuccessResponse)
async def toggle_favorite(id: str, api_key: str = Depends(verify_api_key)):
    try:
        # In real app, get user_id from token
        user_id = "user_123" 
        
        # Check if already favorite
        res = supabase.table("user_profiles").select("favorites").eq("id", user_id).execute()
        favorites = res.data[0].get("favorites", {}) if res.data and res.data[0].get("favorites") else {}
        temple_favs = favorites.get("temples", [])
        
        if id in temple_favs:
            temple_favs.remove(id)
            msg = "Removed from favorites"
        else:
            temple_favs.append(id)
            msg = "Added to favorites"
            
        favorites["temples"] = temple_favs
        supabase.table("user_profiles").update({"favorites": favorites}).eq("id", user_id).execute()
        
        return success_response({"is_favorite": id in temple_favs}, msg)
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

