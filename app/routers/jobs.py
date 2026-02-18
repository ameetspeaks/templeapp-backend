from fastapi import APIRouter, Depends
from datetime import datetime
from app.services.scheduler_service import scheduler
from app.utils.response import success_response, error_response
from app.models.schemas import SuccessResponse
from app.utils.auth import verify_api_key

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.get("/status", response_model=SuccessResponse)
async def job_status(api_key: str = Depends(verify_api_key)):
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": str(job.next_run_time) if job.next_run_time else None
        })
    return success_response(jobs)

@router.post("/trigger/{job_name}", response_model=SuccessResponse)
async def trigger_job(job_name: str, api_key: str = Depends(verify_api_key)):
    job = scheduler.get_job(job_name)
    if job:
        job.modify(next_run_time=datetime.now())
        return success_response(None, f"Job {job_name} triggered")
    return error_response("Job not found", 404)

from app.utils.supabase_client import supabase
from typing import Optional

@router.get("/logs", response_model=SuccessResponse)
async def job_logs(job_name: Optional[str] = None, limit: int = 50, api_key: str = Depends(verify_api_key)):
    try:
        query = supabase.table("job_logs").select("*").order("started_at", desc=True).limit(limit)
        if job_name:
            query = query.eq("job_name", job_name)
        
        res = query.execute()
        return success_response(res.data)
    except Exception as e:
        return error_response(str(e), 500)

from fastapi import BackgroundTasks
from app.services.bulk_panchang_service import BulkPanchangService

@router.post("/seed-2026", response_model=SuccessResponse)
async def seed_2026_panchang(background_tasks: BackgroundTasks, api_key: str = Depends(verify_api_key)):
    """
    Triggers the bulk generation of Panchang for the entire year 2026.
    Runs in background to avoid timeout.
    """
    service = BulkPanchangService()
    background_tasks.add_task(service.generate_2026, "Delhi")
    return success_response(None, "Started 2026 Bulk Generation in background. Check logs for progress.")

@router.get("/debug-panchang", response_model=SuccessResponse)
async def debug_panchang_generation(api_key: str = Depends(verify_api_key)):
    """
    Debug endpoint to run generation for ONE day synchronously and return results/errors.
    """
    try:
        service = BulkPanchangService()
        date_str = "2026-01-01"
        city = "Delhi"
        
        # 1. Base
        calc_data = service.calculator.calculate(date_str, city)
        
        # 2. Gemini
        prompt = f"Generate JSON for {date_str} {city}. Keys: hindi_description, english_description, spiritual_message, festivals (list), vrat."
        ai_data = await service.gemini.generate_json(prompt, model="flash")
        
        # 3. DB
        full_data = {**calc_data, **ai_data}
        if not isinstance(full_data.get('festivals'), list):
             full_data['festivals'] = []
             
        res = supabase.table("panchang_daily").upsert(full_data).execute()
        
        return success_response({
            "status": "success",
            "date": date_str,
            "calc_data": calc_data,
            "ai_data": ai_data,
            "db_result": res.data
        })
    except Exception as e:
        import traceback
        return error_response(f"Debug Failed: {str(e)} | Trace: {traceback.format_exc()}", 500)
