from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.models.schemas import SuccessResponse, Aarti, PaginationResponse
from app.services.gemini_client import GeminiClient
from app.utils.supabase_client import supabase
from app.utils.response import success_response, error_response
from app.utils.auth import verify_api_key

router = APIRouter(prefix="/v1/aartis", tags=["Aarti V1"])
gemini = GeminiClient()

@router.get("", response_model=SuccessResponse)
async def list_aartis(
    q: Optional[str] = None,
    deity: Optional[str] = None,
    lang: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    api_key: str = Depends(verify_api_key)
):
    try:
        query = supabase.table("aartis").select("*", count="exact")
        
        if q:
            query = query.ilike("title", f"%{q}%")
        if deity:
            query = query.eq("deity", deity)
        # lang filter might be complex if it's checking lyrics existence, skip for simple MVP or check if col is not null
            
        start = (page - 1) * page_size
        end = start + page_size - 1
        
        res = query.range(start, end).execute()
        
        # Transform to v1 schema
        items = []
        for item in res.data:
            lyrics = {
                "hi": item.get("lyrics_hindi"),
                "en": item.get("lyrics_english_transliteration") or item.get("lyrics_english_meaning")
            }
            items.append({
                "id": item["id"],
                "title": item["title"],
                "deity": item["deity"],
                "audio_url": item.get("audio_url"),
                "duration_sec": item.get("duration_seconds"),
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
async def get_aarti(id: str, api_key: str = Depends(verify_api_key)):
    try:
        res = supabase.table("aartis").select("*").eq("id", id).execute()
        if not res.data:
            return error_response("Not found", 404)
        
        item = res.data[0]
        lyrics = {
            "hi": item.get("lyrics_hindi"),
            "en": item.get("lyrics_english_transliteration")
        }
        
        return success_response({
            "id": item["id"],
            "title": item["title"],
            "deity": item["deity"],
            "audio_url": item.get("audio_url"),
            "duration_sec": item.get("duration_seconds"),
            "lyrics": lyrics,
            "significance": item.get("significance"),
            "best_time": item.get("best_time")
        })
    except Exception as e:
        return error_response(str(e), 500)

@router.get("/{id}/lyrics", response_model=SuccessResponse)
async def get_aarti_lyrics(id: str, lang: str = "hi", api_key: str = Depends(verify_api_key)):
    try:
        col = "lyrics_hindi" if lang == "hi" else "lyrics_english_transliteration"
        res = supabase.table("aartis").select(col).eq("id", id).execute()
        
        if not res.data:
            return error_response("Not found", 404)
            
        return success_response({"lyrics": res.data[0].get(col)})
    except Exception as e:
        return error_response(str(e), 500)

@router.get("/admin/list", response_model=SuccessResponse)
async def list_aartis_admin(
    q: Optional[str] = None,
    deity: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    try:
        query = supabase.table("aartis").select("*", count="exact")
        if q:
            query = query.ilike("title", f"%{q}%")
        if deity:
            query = query.eq("deity", deity)
            
        res = query.execute()
        return success_response({"items": res.data, "total": res.count})
    except Exception as e:
        return error_response(str(e), 500)

@router.post("", response_model=SuccessResponse)
async def add_aarti(data: dict, api_key: str = Depends(verify_api_key)):
    try:
        # Default status
        if "status" not in data:
            data["status"] = "pending_audio"
        res = supabase.table("aartis").insert(data).execute()
        return success_response(res.data[0] if res.data else data)
    except Exception as e:
        return error_response(str(e), 500)

@router.put("/{id}", response_model=SuccessResponse)
async def update_aarti(id: str, data: dict, api_key: str = Depends(verify_api_key)):
    try:
        res = supabase.table("aartis").update(data).eq("id", id).execute()
        return success_response(res.data[0] if res.data else data)
    except Exception as e:
        return error_response(str(e), 500)

@router.delete("/{id}", response_model=SuccessResponse)
async def delete_aarti(id: str, api_key: str = Depends(verify_api_key)):
    try:
        supabase.table("aartis").delete().eq("id", id).execute()
        return success_response(None, "Deleted")
    except Exception as e:
        return error_response(str(e), 500)

@router.post("/{id}/generate-lyrics", response_model=SuccessResponse)
async def generate_aarti_lyrics_endpoint(id: str, api_key: str = Depends(verify_api_key)):
    try:
        res = supabase.table("aartis").select("*").eq("id", id).execute()
        if not res.data:
            return error_response("Aarti not found", 404)
        aarti = res.data[0]
        
        prompt = f"""
        Generate full authentic lyrics for the Aarti: "{aarti['title']}" for deity "{aarti['deity']}".
        Return JSON with: 
        - lyrics_hindi: The full lyrics in Hindi (Devanagari).
        - lyrics_english_transliteration: Romanized Hindi lyrics.
        - significance: A short paragraph about this aarti.
        """
        
        ai_data = await gemini.generate_json(prompt, model="flash")
        
        update_data = {
            "lyrics_hindi": ai_data.get("lyrics_hindi"),
            "lyrics_english_transliteration": ai_data.get("lyrics_english_transliteration"),
            "significance": ai_data.get("significance"),
        }
        
        supabase.table("aartis").update(update_data).eq("id", id).execute()
        return success_response(update_data, "Lyrics generated")
    except Exception as e:
        return error_response(str(e), 500)

@router.post("/{id}/fetch-audio", response_model=SuccessResponse)
async def fetch_aarti_audio_endpoint(id: str, api_key: str = Depends(verify_api_key)):
    try:
        # Mock logic or real fetch logic
        # For now, let's just mark as 'complete' if they have a URL, or set a placeholder
        update_data = {
            "status": "complete",
            "audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3" # Placeholder
        }
        supabase.table("aartis").update(update_data).eq("id", id).execute()
        return success_response(update_data, "Audio fetched (simulated)")
    except Exception as e:
        return error_response(str(e), 500)

