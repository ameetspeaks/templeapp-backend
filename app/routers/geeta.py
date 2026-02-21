from fastapi import APIRouter, Depends, HTTPException, Header, Query
from typing import List, Optional
from app.models.schemas import (
    SuccessResponse, GeetaChapterSchema, GeetaShlokaSchema,
    ReadingProgress, SaveProgressRequest
)
from app.utils.supabase_client import supabase
from app.utils.response import success_response, error_response
from app.utils.auth import verify_api_key

router = APIRouter(prefix="/v1/geeta", tags=["Geeta V1"])


# ---------- Chapters ----------

@router.get("/chapters", response_model=SuccessResponse)
async def get_all_chapters(api_key: str = Depends(verify_api_key)):
    """Return all 18 Bhagavad Gita chapters with metadata."""
    try:
        res = supabase.table("geeta_chapters").select("*").order("chapter_number").execute()
        return success_response(res.data or [])
    except Exception as e:
        return error_response(str(e), 500)


@router.get("/chapters/{chapter_number}", response_model=SuccessResponse)
async def get_chapter(chapter_number: int, api_key: str = Depends(verify_api_key)):
    """Return a single chapter's metadata."""
    try:
        res = supabase.table("geeta_chapters").select("*").eq("chapter_number", chapter_number).limit(1).execute()
        if not res.data:
            return error_response(f"Chapter {chapter_number} not found", 404)
        return success_response(res.data[0])
    except Exception as e:
        return error_response(str(e), 500)


# ---------- Shlokas ----------

@router.get("/chapters/{chapter_number}/shlokas", response_model=SuccessResponse)
async def get_chapter_shlokas(
    chapter_number: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    api_key: str = Depends(verify_api_key)
):
    """Return all shlokas for a given chapter (paginated)."""
    try:
        offset = (page - 1) * page_size

        # Total count
        count_res = supabase.table("geeta_shlokas")\
            .select("id", count="exact", head=True)\
            .eq("chapter_number", chapter_number)\
            .execute()

        # Paginated data
        res = supabase.table("geeta_shlokas")\
            .select("*")\
            .eq("chapter_number", chapter_number)\
            .order("verse_number")\
            .range(offset, offset + page_size - 1)\
            .execute()

        return success_response({
            "chapter_number": chapter_number,
            "page": page,
            "page_size": page_size,
            "total": count_res.count or 0,
            "shlokas": res.data or [],
        })
    except Exception as e:
        return error_response(str(e), 500)


@router.get("/shlokas/{shloka_id}", response_model=SuccessResponse)
async def get_shloka(shloka_id: str, api_key: str = Depends(verify_api_key)):
    """Return a specific shloka by ID (e.g. '2.47')."""
    try:
        res = supabase.table("geeta_shlokas").select("*").eq("id", shloka_id).limit(1).execute()
        if not res.data:
            return error_response(f"Shloka '{shloka_id}' not found", 404)
        return success_response(res.data[0])
    except Exception as e:
        return error_response(str(e), 500)


@router.get("/search", response_model=SuccessResponse)
async def search_shlokas(
    q: str = Query(..., min_length=2),
    api_key: str = Depends(verify_api_key)
):
    """Search shlokas by keyword across translations, Sanskrit text, and tags."""
    try:
        # Full-text style search using ilike on multiple columns
        res = supabase.table("geeta_shlokas")\
            .select("id, chapter_number, verse_number, sanskrit_text, hindi_translation, english_translation, tags")\
            .or_(f"hindi_translation.ilike.%{q}%,english_translation.ilike.%{q}%,sanskrit_text.ilike.%{q}%")\
            .limit(20)\
            .execute()
        return success_response(res.data or [])
    except Exception as e:
        return error_response(str(e), 500)


# ---------- Reading Progress ----------

@router.get("/progress", response_model=SuccessResponse)
async def get_reading_progress(
    authorization: Optional[str] = Header(None),
    api_key: str = Depends(verify_api_key)
):
    """Get the authenticated user's Gita reading progress."""
    try:
        if not authorization or not authorization.startswith("Bearer "):
            return error_response("Authorization header required", 401)

        token = authorization.split(" ")[1]
        user_res = supabase.auth.get_user(token)
        if not user_res or not user_res.user:
            return error_response("Invalid or expired token", 401)

        user_id = user_res.user.id
        res = supabase.table("user_reading_progress").select("*").eq("user_id", user_id).limit(1).execute()

        if not res.data:
            return success_response({"user_id": user_id, "last_chapter": 1, "last_verse": 1})
        return success_response(res.data[0])
    except Exception as e:
        return error_response(str(e), 500)


@router.post("/progress", response_model=SuccessResponse)
async def save_reading_progress(
    body: SaveProgressRequest,
    authorization: Optional[str] = Header(None),
    api_key: str = Depends(verify_api_key)
):
    """Save the authenticated user's Gita reading progress."""
    try:
        if not authorization or not authorization.startswith("Bearer "):
            return error_response("Authorization header required", 401)

        token = authorization.split(" ")[1]
        user_res = supabase.auth.get_user(token)
        if not user_res or not user_res.user:
            return error_response("Invalid or expired token", 401)

        user_id = user_res.user.id
        payload = {
            "user_id": user_id,
            "last_chapter": body.chapter,
            "last_verse": body.verse,
        }
        supabase.table("user_reading_progress").upsert(payload, on_conflict="user_id").execute()

        return success_response({"user_id": user_id, "last_chapter": body.chapter, "last_verse": body.verse})
    except Exception as e:
        return error_response(str(e), 500)
