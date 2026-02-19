from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.models.schemas import SuccessResponse, SearchResult, PaginationResponse
from app.utils.supabase_client import supabase
from app.utils.response import success_response, error_response
from app.utils.auth import verify_api_key
import asyncio

router = APIRouter(prefix="/v1/search", tags=["Search V1"])

@router.get("/suggestions", response_model=SuccessResponse)
async def search_suggestions(
    q: str,
    limit: int = 8,
    api_key: str = Depends(verify_api_key)
):
    try:
        if not q or len(q) < 2:
            return success_response({"items": []})
            
        # Basic implementation: Search names in Temples, Aartis
        
        temples = supabase.table("temples").select("name").ilike("name", f"%{q}%").limit(limit).execute()
        aartis = supabase.table("aartis").select("title").ilike("title", f"%{q}%").limit(limit).execute()
        
        items = [t['name'] for t in temples.data] + [a['title'] for a in aartis.data]
        # De-duplicate and limit
        items = list(dict.fromkeys(items))[:limit]
        
        return success_response({"items": items})
    except Exception as e:
        return error_response(str(e), 500)

@router.get("", response_model=SuccessResponse)
async def search_all(
    q: str,
    page: int = 1,
    page_size: int = 20,
    api_key: str = Depends(verify_api_key)
):
    try:
        # Search across multiple tables
        # MVP: Simple ILIKE queries on key tables
        
        limit_per_type = 10 
        
        f_temples = supabase.table("temples").select("id, name, city").ilike("name", f"%{q}%").limit(limit_per_type).execute()
        f_aartis = supabase.table("aartis").select("id, title").ilike("title", f"%{q}%").limit(limit_per_type).execute()
        f_bhajans = supabase.table("bhajans").select("id, title").ilike("title", f"%{q}%").limit(limit_per_type).execute()
        
        results = []
        for t in f_temples.data:
            results.append({
                "type": "temple",
                "id": t["id"],
                "title": t["name"],
                "subtitle": t["city"]
            })
            
        for a in f_aartis.data:
            results.append({
                "type": "aarti",
                "id": a["id"],
                "title": a["title"]
            })
            
        for b in f_bhajans.data:
            results.append({
                "type": "bhajan",
                "id": b["id"],
                "title": b["title"]
            })
            
        # Pagination (in-memory for MVP)
        total = len(results)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_results = results[start:end]
        
        return success_response({
            "items": paginated_results,
            "page": page,
            "page_size": page_size,
            "total": total
        })
    except Exception as e:
        return error_response(str(e), 500)
