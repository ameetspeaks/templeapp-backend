from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.models.schemas import SuccessResponse, Bhajan, PaginationResponse
from app.utils.supabase_client import supabase
from app.utils.response import success_response, error_response
from app.utils.auth import verify_api_key
from pydantic import BaseModel

class BhajanCreateRequest(BaseModel):
    title: str
    deity: Optional[str] = None
    singer: Optional[str] = None
    category: Optional[str] = None
    audio_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    image_url: Optional[str] = None
    lyrics_hindi: Optional[str] = None
    lyrics_english: Optional[str] = None

class BhajanUpdateRequest(BaseModel):
    title: Optional[str] = None
    deity: Optional[str] = None
    singer: Optional[str] = None
    category: Optional[str] = None
    audio_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    image_url: Optional[str] = None
    lyrics_hindi: Optional[str] = None
    lyrics_english: Optional[str] = None

router = APIRouter(prefix="/v1/bhajans", tags=["Bhajan V1"])

@router.get("", response_model=SuccessResponse)
async def list_bhajans(
    q: Optional[str] = None,
    deity: Optional[str] = None,
    category: Optional[str] = None,
    singer: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    api_key: str = Depends(verify_api_key)
):
    try:
        query = supabase.table("bhajans").select("*", count="exact")
        
        if q:
            query = query.ilike("title", f"%{q}%")
        if deity:
            query = query.eq("deity", deity)
        if category:
            query = query.eq("category", category)
        if singer:
            query = query.ilike("singer", f"%{singer}%")
            
        start = (page - 1) * page_size
        end = start + page_size - 1
        
        res = query.range(start, end).execute()
        
        # Transform keys if needed
        items = []
        for item in res.data:
            lyrics = {
                "hi": item.get("lyrics_hindi"),
                "en": item.get("lyrics_english")
            }
            items.append({
                "id": item["id"],
                "title": item["title"],
                "singer": item.get("singer"),
                "deity": item.get("deity"),
                "category": item.get("category"),
                "audio_url": item.get("audio_url"),
                "duration_sec": item.get("duration_seconds"),
                "image_url": item.get("image_url"),
                "lyrics": lyrics
            })
            
        return success_response({
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": res.count
        })
    except Exception as e:
        return error_response(str(e), 500)

@router.get("/{id}", response_model=SuccessResponse)
async def get_bhajan(id: str, api_key: str = Depends(verify_api_key)):
    try:
        res = supabase.table("bhajans").select("*").eq("id", id).execute()
        if not res.data:
            return error_response("Not found", 404)
        
        item = res.data[0]
        lyrics = {
            "hi": item.get("lyrics_hindi"),
            "en": item.get("lyrics_english")
        }
        
        return success_response({
            "id": item["id"],
            "title": item["title"],
            "singer": item.get("singer"),
            "deity": item.get("deity"),
            "category": item.get("category"),
            "audio_url": item.get("audio_url"),
            "duration_sec": item.get("duration_seconds"),
            "image_url": item.get("image_url"),
            "lyrics": lyrics
        })
    except Exception as e:
        return error_response(str(e), 500)


# --- Admin CRUD ---

@router.post("", response_model=SuccessResponse)
async def create_bhajan(body: BhajanCreateRequest, api_key: str = Depends(verify_api_key)):
    try:
        data = body.model_dump(exclude_none=True)
        res = supabase.table("bhajans").insert(data).execute()
        return success_response(res.data[0] if res.data else data, "Bhajan created")
    except Exception as e:
        return error_response(str(e), 500)

@router.put("/{id}", response_model=SuccessResponse)
async def update_bhajan(id: str, body: BhajanUpdateRequest, api_key: str = Depends(verify_api_key)):
    try:
        data = body.model_dump(exclude_none=True)
        if not data:
            return error_response("No fields to update", 400)
        res = supabase.table("bhajans").update(data).eq("id", id).execute()
        if not res.data:
            return error_response("Not found", 404)
        return success_response(res.data[0], "Bhajan updated")
    except Exception as e:
        return error_response(str(e), 500)

@router.delete("/{id}", response_model=SuccessResponse)
async def delete_bhajan(id: str, api_key: str = Depends(verify_api_key)):
    try:
        supabase.table("bhajans").delete().eq("id", id).execute()
        return success_response(None, "Bhajan deleted")
    except Exception as e:
        return error_response(str(e), 500)
