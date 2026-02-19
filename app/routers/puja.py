from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.models.schemas import SuccessResponse, PujaGuide, PujaSamagri
from app.utils.supabase_client import supabase
from app.utils.response import success_response, error_response
from app.utils.auth import verify_api_key

router = APIRouter(prefix="/v1/puja", tags=["Puja V1"])

@router.get("/guides", response_model=SuccessResponse)
async def list_puja_guides(
    category: Optional[str] = None, # daily, festival, vrat
    q: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    api_key: str = Depends(verify_api_key)
):
    try:
        query = supabase.table("puja_guides").select("id, title, category, deity, image_urls", count="exact")
        
        if q:
            query = query.ilike("title", f"%{q}%")
        if category:
            query = query.eq("category", category)
            
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

@router.get("/guides/{id}", response_model=SuccessResponse)
async def get_puja_guide(id: str, api_key: str = Depends(verify_api_key)):
    try:
        # Fetch guide details
        guide_res = supabase.table("puja_guides").select("*").eq("id", id).execute()
        if not guide_res.data:
            return error_response("Not found", 404)
        guide = guide_res.data[0]
        
        # Fetch steps
        steps_res = supabase.table("puja_steps").select("*").eq("guide_id", id).order("step_index").execute()
        guide["steps"] = steps_res.data
        
        # Fetch samagri
        samagri_res = supabase.table("puja_samagri").select("name, qty, is_optional").eq("guide_id", id).execute()
        guide["samagri"] = samagri_res.data
        
        return success_response(guide)
    except Exception as e:
        return error_response(str(e), 500)

@router.get("/guides/{id}/samagri", response_model=SuccessResponse)
async def get_puja_samagri(id: str, api_key: str = Depends(verify_api_key)):
    try:
         res = supabase.table("puja_samagri").select("*").eq("guide_id", id).execute()
         return success_response({"samagri": res.data})
    except Exception as e:
        return error_response(str(e), 500)

# Progress endpoints (requires user auth context, skipping strict auth check impl for now, just schema)
@router.post("/progress", response_model=SuccessResponse)
async def update_progress(
    guide_id: str, 
    step_index: int, 
    completed: bool = True,
    user_id: Optional[str] = None, # Should come from auth token really
    api_key: str = Depends(verify_api_key)
):
    # This requires a proper user session. For MVP, we might just return success or mock.
    # To implement for real:
    # if not user_id: return error_response("Unauthorized", 401)
    # upsert into user_puja_progress
    return success_response({"status": "updated"}, "Progress updated")
