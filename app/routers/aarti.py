from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.models.schemas import AartiGenerateRequest, AartiBatchGenerateRequest, AartiFetchAudioRequest, AartiFetchAudioUrlRequest, SuccessResponse
from app.services.gemini_client import GeminiClient
from app.services.audio_pipeline import AudioPipeline
from app.utils.supabase_client import supabase
from app.utils.response import success_response, error_response
from app.utils.auth import verify_api_key

router = APIRouter(prefix="/aarti", tags=["Aarti"])
gemini = GeminiClient()
audio_pipeline = AudioPipeline()

@router.post("/generate-lyrics", response_model=SuccessResponse)
async def generate_lyrics(request: AartiGenerateRequest, api_key: str = Depends(verify_api_key)):
    try:
        prompt = f"""
        Generate authentic lyrics for {request.title} aarti of {request.deity}. Type: {request.aarti_type}.
        Output JSON: lyrics_hindi, lyrics_english_transliteration, lyrics_english_meaning, significance, best_time, estimated_duration_minutes.
        """
        ai_data = await gemini.generate_json(prompt, model="pro")
        
        db_data = {
            "title": request.title,
            "deity": request.deity,
            "aarti_type": request.aarti_type,
            "language": request.language,
            **ai_data,
            "status": "pending_audio"
        }
        res = supabase.table("aartis").insert(db_data).execute()
        return success_response(res.data[0], "Lyrics generated")
    except Exception as e:
        return error_response(str(e), 500)

@router.post("/fetch-audio/{aarti_id}", response_model=SuccessResponse)
async def fetch_audio(aarti_id: str, api_key: str = Depends(verify_api_key)):
    try:
        res = supabase.table("aartis").select("*").eq("id", aarti_id).execute()
        if not res.data:
            return error_response("Aarti not found", 404)
        aarti = res.data[0]
        
        result = audio_pipeline.search_and_fetch_audio(aarti['title'], aarti['deity'], aarti_id)
        
        update_data = {
            "audio_url": result['cloudinary_url'],
            "audio_source_url": result['source_url'],
            "duration_seconds": result['duration_seconds'],
            "status": "complete"
        }
        supabase.table("aartis").update(update_data).eq("id", aarti_id).execute()
        return success_response(update_data, "Audio fetched")
    except Exception as e:
        return error_response(str(e), 500)

@router.get("/list", response_model=SuccessResponse)
async def list_aartis(deity: str = None, status: str = None, page: int = 1, api_key: str = Depends(verify_api_key)):
    try:
        query = supabase.table("aartis").select("*")
        if deity:
            query = query.eq("deity", deity)
        if status:
            query = query.eq("status", status)
        res = query.execute()
        return success_response(res.data)
    except Exception as e:
        return error_response(str(e), 500)

@router.get("/{id}", response_model=SuccessResponse)
async def get_aarti(id: str, api_key: str = Depends(verify_api_key)):
    try:
        res = supabase.table("aartis").select("*").eq("id", id).execute()
        if not res.data:
            return error_response("Aarti not found", 404)
        return success_response(res.data[0])
    except Exception as e:
        return error_response(str(e), 500)
