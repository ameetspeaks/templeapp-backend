from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta
import asyncio
from app.models.schemas import MuhuratCalculateRequest, MuhuratMonthlyReportRequest, SuccessResponse
from app.services.panchang_calculator import PanchangCalculator
from app.services.gemini_client import GeminiClient
from app.utils.supabase_client import supabase
from app.utils.response import success_response, error_response
from app.utils.auth import verify_api_key

router = APIRouter(prefix="/muhurat", tags=["Muhurat"])
panchang_calc = PanchangCalculator()
gemini = GeminiClient()

@router.post("/calculate", response_model=SuccessResponse)
async def calculate_muhurat(request: MuhuratCalculateRequest, api_key: str = Depends(verify_api_key)):
    try:
        # Generate dates for the month
        start_date = datetime(request.year, request.month, 1)
        if request.month == 12:
            next_month = datetime(request.year + 1, 1, 1)
        else:
            next_month = datetime(request.year, request.month + 1, 1)
        
        days_in_month = (next_month - start_date).days
        
        candidates = []
        for i in range(days_in_month):
            curr_date = start_date + timedelta(days=i)
            date_str = curr_date.strftime("%Y-%m-%d")
            p = panchang_calc.calculate(date_str, request.city)
            
            # Filter logic
            t_idx = p['tithi_index']
            if t_idx in [29, 28, 22]: 
                continue
            
            candidates.append(p)
            
        # Select top 7 candidates
        shortlist = candidates[:7]
        
        results = []
        for day in shortlist:
            prompt = f"""
            Analyze muhurat for {request.muhurat_type} on {day['date']} in {request.city}.
            Panchang: {day}.
            Validate and score (1.0-5.0). Assign auspicious time window. Write 80-word Vedic reasoning.
            Output JSON: {{ "score": 4.5, "time_window": "10:00-12:00", "reasoning": "..." }}
            """
            ai_data = await gemini.generate_json(prompt, model="pro")
            results.append({**day, **ai_data})
            
        # Sort by score
        results.sort(key=lambda x: x.get('score', 0), reverse=True)
        top_5 = results[:5]
        
        # Save to Supabase
        for item in top_5:
            db_data = {
                "type": request.muhurat_type,
                "date": item['date'],
                "city": request.city,
                "start_time": item.get('time_window', '').split('-')[0] if item.get('time_window') else None,
                "end_time": item.get('time_window', '').split('-')[-1] if item.get('time_window') else None,
                "score": item.get('score'),
                "reasoning": item.get('reasoning'),
                "created_at": datetime.now().isoformat()
            }
            supabase.table("muhurats").insert(db_data).execute()
            
        return success_response(top_5, "Muhurats calculated")
    except Exception as e:
        return error_response(str(e), 500)

@router.get("/upcoming", response_model=SuccessResponse)
async def upcoming_muhurats(type: str, days: int = 30, city: str = "Delhi", api_key: str = Depends(verify_api_key)):
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        end = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        res = supabase.table("muhurats").select("*").eq("type", type).eq("city", city).gte("date", today).lte("date", end).order("date").execute()
        return success_response(res.data)
    except Exception as e:
        return error_response(str(e), 500)

@router.get("/list", response_model=SuccessResponse)
async def list_muhurats(type: str, month: int, year: int, api_key: str = Depends(verify_api_key)):
    try:
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{month+1:02d}-01"
            
        res = supabase.table("muhurats").select("*").eq("type", type).gte("date", start_date).lt("date", end_date).execute()
        return success_response(res.data)
    except Exception as e:
        return error_response(str(e), 500)
