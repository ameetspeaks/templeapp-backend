from fastapi import APIRouter, Depends, HTTPException, Header
from typing import List, Optional
from datetime import datetime, timedelta
from app.models.schemas import SuccessResponse, DailyGyanEntry, BookmarkRequest, BookmarkResponse
from app.utils.supabase_client import supabase
from app.utils.response import success_response, error_response
from app.utils.auth import verify_api_key

router = APIRouter(prefix="/v1/gyan", tags=["Gyan V1"])


def _parse_gyan(row: dict) -> dict:
    """Normalize a DB row into the API shape."""
    return {
        "id": row.get("id"),
        "date": str(row.get("date", "")),
        "chapter_number": row.get("chapter_number"),
        "verse_number": row.get("verse_number"),
        "sanskrit_text": row.get("sanskrit_text", ""),
        "transliteration": row.get("transliteration"),
        "hindi_translation": row.get("hindi_translation", ""),
        "english_translation": row.get("english_translation", ""),
        "hindi_meaning": row.get("hindi_meaning"),
        "english_meaning": row.get("english_meaning"),
        "daily_message": row.get("daily_message"),
        "daily_message_hindi": row.get("daily_message_hindi"),
        "practice_for_today": row.get("practice_for_today"),
        "practice_for_today_hindi": row.get("practice_for_today_hindi"),
        "source": row.get("source", "Bhagavad Gita"),
        "tags": row.get("tags") or [],
    }


@router.get("/today", response_model=SuccessResponse)
async def get_todays_gyan(
    date: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """Fetch Aaj Ka Gyan — the daily spiritual wisdom card."""
    try:
        target_date = date or datetime.now().strftime("%Y-%m-%d")

        res = supabase.table("daily_gyan").select("*").eq("date", target_date).limit(1).execute()

        if not res.data:
            # Fallback: return the most recent gyan available
            fallback = supabase.table("daily_gyan").select("*").order("date", desc=True).limit(1).execute()
            if not fallback.data:
                return error_response("No daily gyan available yet. Please run the generation script.", 404)
            return success_response(_parse_gyan(fallback.data[0]))

        return success_response(_parse_gyan(res.data[0]))

    except Exception as e:
        return error_response(str(e), 500)


@router.get("/history", response_model=SuccessResponse)
async def get_gyan_history(
    days: int = 7,
    api_key: str = Depends(verify_api_key)
):
    """Fetch Gyan history for the past N days (default 7)."""
    try:
        since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        res = supabase.table("daily_gyan").select("*").gte("date", since).order("date", desc=True).execute()
        return success_response([_parse_gyan(r) for r in (res.data or [])])
    except Exception as e:
        return error_response(str(e), 500)


@router.post("/bookmark", response_model=SuccessResponse)
async def bookmark_shloka(
    body: BookmarkRequest,
    authorization: Optional[str] = Header(None),
    api_key: str = Depends(verify_api_key)
):
    """Bookmark a shloka for the authenticated user."""
    try:
        if not authorization or not authorization.startswith("Bearer "):
            return error_response("Authorization header required", 401)

        token = authorization.split(" ")[1]
        user_res = supabase.auth.get_user(token)
        if not user_res or not user_res.user:
            return error_response("Invalid or expired token", 401)

        user_id = user_res.user.id

        # Upsert bookmark (ignores duplicate)
        payload = {"user_id": user_id, "shloka_id": body.shloka_id}
        result = supabase.table("user_shloka_bookmarks").upsert(payload, on_conflict="user_id,shloka_id").execute()

        return success_response({
            "shloka_id": body.shloka_id,
            "user_id": user_id,
            "bookmarked": True
        })
    except Exception as e:
        return error_response(str(e), 500)


@router.delete("/bookmark/{shloka_id}", response_model=SuccessResponse)
async def remove_bookmark(
    shloka_id: str,
    authorization: Optional[str] = Header(None),
    api_key: str = Depends(verify_api_key)
):
    """Remove a bookmark for the authenticated user."""
    try:
        if not authorization or not authorization.startswith("Bearer "):
            return error_response("Authorization header required", 401)

        token = authorization.split(" ")[1]
        user_res = supabase.auth.get_user(token)
        if not user_res or not user_res.user:
            return error_response("Invalid or expired token", 401)

        user_id = user_res.user.id
        supabase.table("user_shloka_bookmarks").delete().eq("user_id", user_id).eq("shloka_id", shloka_id).execute()

        return success_response({"shloka_id": shloka_id, "bookmarked": False})
    except Exception as e:
        return error_response(str(e), 500)


@router.get("/bookmarks", response_model=SuccessResponse)
async def get_bookmarks(
    authorization: Optional[str] = Header(None),
    api_key: str = Depends(verify_api_key)
):
    """Get all bookmarked shlokas for the authenticated user."""
    try:
        if not authorization or not authorization.startswith("Bearer "):
            return error_response("Authorization header required", 401)

        token = authorization.split(" ")[1]
        user_res = supabase.auth.get_user(token)
        if not user_res or not user_res.user:
            return error_response("Invalid or expired token", 401)

        user_id = user_res.user.id

        # Join bookmarks with shloka data
        bookmarks_res = supabase.table("user_shloka_bookmarks")\
            .select("shloka_id, created_at, geeta_shlokas(*)")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .execute()

        result = []
        for b in (bookmarks_res.data or []):
            shloka = b.get("geeta_shlokas") or {}
            result.append({
                "shloka_id": b.get("shloka_id"),
                "bookmarked_at": b.get("created_at"),
                "shloka": shloka,
            })

        return success_response(result)
    except Exception as e:
        return error_response(str(e), 500)
