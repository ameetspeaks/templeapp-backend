from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import datetime, timedelta
from app.models.schemas import PanchangRequest, PanchangRangeRequest, SuccessResponse
from app.services.panchang_calculator import PanchangCalculator
from app.services.gemini_client import GeminiClient
from app.utils.supabase_client import supabase
from app.utils.response import success_response, error_response
from app.utils.auth import verify_api_key

router = APIRouter(prefix="/panchang", tags=["Panchang"])
panchang_calc = PanchangCalculator()
gemini = GeminiClient()

@router.post("/generate", response_model=SuccessResponse)
async def generate_panchang(request: PanchangRequest, api_key: str = Depends(verify_api_key)):
    try:
        # 1. Calculate
        calc_data = panchang_calc.calculate(request.date, request.city)
        
        # 2. AI Enrich
        prompt = f"""
        Generate a daily panchang description based on this data: {calc_data}.
        Include any major Hindu festival falling on this tithi/date if applicable.
        
        Output JSON:
        {{
            "hindi_description": "120 words devotional Pandit style with blessings",
            "english_description": "120 words explanation",
            "spiritual_message": "2 sentences quote or wisdom",
            "festivals": ["List of festivals if any, else empty"]
        }}
        """
        
        ai_data = await gemini.generate_json(prompt, model="flash")
        
        # 3. Merge
        full_data = {**calc_data, **ai_data}
        
        # 4. Save to Supabase
        # Check if exists
        res = supabase.table("panchang_daily").select("id").eq("date", request.date).eq("city", request.city).execute()
        
        if res.data:
            supabase.table("panchang_daily").update(full_data).eq("id", res.data[0]['id']).execute()
        else:
            supabase.table("panchang_daily").insert(full_data).execute()
            
        return success_response(full_data, "Panchang generated successfully")
        
    except Exception as e:
        return error_response(str(e), 500)

@router.post("/generate-range", response_model=SuccessResponse)
async def generate_panchang_range(request: PanchangRangeRequest, api_key: str = Depends(verify_api_key)):
    try:
        start = datetime.strptime(request.start_date, "%Y-%m-%d")
        end = datetime.strptime(request.end_date, "%Y-%m-%d")
        curr = start
        results = []
        
        while curr <= end:
            date_str = curr.strftime("%Y-%m-%d")
            
            calc_data = panchang_calc.calculate(date_str, request.city)
            prompt = f"""
            Generate daily panchang description for {calc_data}.
            Output JSON with hindi_description, english_description, spiritual_message, festivals.
            """
            ai_data = await gemini.generate_json(prompt, model="flash")
            full_data = {**calc_data, **ai_data}
            
            res = supabase.table("panchang_daily").select("id").eq("date", date_str).eq("city", request.city).execute()
            if res.data:
                supabase.table("panchang_daily").update(full_data).eq("id", res.data[0]['id']).execute()
            else:
                supabase.table("panchang_daily").insert(full_data).execute()
            
            results.append(full_data)
            curr += timedelta(days=1)
            
        return success_response({"count": len(results)}, "Range generation completed")
    except Exception as e:
        return error_response(str(e), 500)

@router.get("/list", response_model=SuccessResponse)
async def list_panchang(month: int, year: int, city: str = "Delhi", api_key: str = Depends(verify_api_key)):
    try:
        # Construct start and end dates
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{month+1:02d}-01"
            
        res = supabase.table("panchang_daily").select("*").eq("city", city).gte("date", start_date).lt("date", end_date).execute()
        return success_response(res.data)
    except Exception as e:
        return error_response(str(e), 500)

@router.get("/{date}", response_model=SuccessResponse)
async def get_panchang(date: str, city: str = "Delhi", api_key: str = Depends(verify_api_key)):
    try:
        res = supabase.table("panchang_daily").select("*").eq("date", date).eq("city", city).execute()
        if not res.data:
            return error_response("Panchang not found", 404)
        return success_response(res.data[0])
    except Exception as e:
        return error_response(str(e), 500)

@router.delete("/{date}", response_model=SuccessResponse)
async def delete_panchang(date: str, city: str = "Delhi", api_key: str = Depends(verify_api_key)):
    try:
        supabase.table("panchang_daily").delete().eq("date", date).eq("city", city).execute()
        return success_response(None, "Deleted successfully")
    except Exception as e:
        return error_response(str(e), 500)
