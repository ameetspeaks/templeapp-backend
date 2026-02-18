from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime
import asyncio
from app.models.schemas import TempleAddRequest, TempleEnrichRequest, TempleBulkEnrichRequest, SuccessResponse
from app.services.gemini_client import GeminiClient
from app.utils.supabase_client import supabase
from app.utils.response import success_response, error_response
from app.utils.auth import verify_api_key

router = APIRouter(prefix="/temple", tags=["Temples"])
gemini = GeminiClient()

@router.post("/add", response_model=SuccessResponse)
async def add_temple(request: TempleAddRequest, api_key: str = Depends(verify_api_key)):
    try:
        data = request.dict(exclude_none=True)
        data["status"] = "pending"
        res = supabase.table("temples").insert(data).execute()
        return success_response(res.data[0], "Temple added")
    except Exception as e:
        return error_response(str(e), 500)

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
        Output JSON: history, significance, darshan_timings, puja_timings, major_festivals, how_to_reach, nearby_attractions, interesting_facts, dress_code, photography_allowed, entry_fee, best_time_to_visit.
        """
        
        ai_data = await gemini.generate_json(prompt, model="pro")
        
        update_data = {
            **ai_data,
            "status": "enriched",
            "enriched_at": datetime.now().isoformat()
        }
        
        supabase.table("temples").update(update_data).eq("id", temple_id).execute()
        return success_response(update_data, "Enriched")
    except Exception as e:
        return error_response(str(e), 500)

@router.post("/bulk-enrich", response_model=SuccessResponse)
async def bulk_enrich(request: TempleBulkEnrichRequest, api_key: str = Depends(verify_api_key)):
    try:
        res = supabase.table("temples").select("*").eq("status", "pending").limit(request.limit).execute()
        temples = res.data
        
        processed = 0
        failed = 0
        ids = []
        
        for temple in temples:
            try:
                prompt = f"Generate JSON info for {temple['name']}, {temple['deity']} in {temple['city']}."
                ai_data = await gemini.generate_json(prompt, model="flash") # Using flash for bulk
                
                update_data = {
                    **ai_data,
                    "status": "enriched",
                    "enriched_at": datetime.now().isoformat()
                }
                supabase.table("temples").update(update_data).eq("id", temple['id']).execute()
                processed += 1
                ids.append(temple['id'])
                await asyncio.sleep(2)
            except:
                failed += 1
                
        return success_response({"processed": processed, "failed": failed, "ids": ids})
    except Exception as e:
        return error_response(str(e), 500)

@router.get("/list", response_model=SuccessResponse)
async def list_temples(status: Optional[str] = None, state: Optional[str] = None, page: int = 1, limit: int = 25, api_key: str = Depends(verify_api_key)):
    try:
        query = supabase.table("temples").select("id, name, city, state, status")
        if status:
            query = query.eq("status", status)
        if state:
            query = query.eq("state", state)
            
        start = (page - 1) * limit
        end = start + limit - 1
        res = query.range(start, end).execute()
        return success_response(res.data)
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

@router.get("/stats", response_model=SuccessResponse)
async def temple_stats(api_key: str = Depends(verify_api_key)):
    try:
        # Supabase doesn't support complex aggregation easily via simple client
        # We can just fetch counts or use RPC if defined
        # For now returning placeholder or fetching all status (inefficient but works for small data)
        # Using count="exact", head=True
        pending = supabase.table("temples").select("*", count="exact", head=True).eq("status", "pending").execute().count
        enriched = supabase.table("temples").select("*", count="exact", head=True).eq("status", "enriched").execute().count
        return success_response({"pending": pending, "enriched": enriched})
    except Exception as e:
        return error_response(str(e), 500)
