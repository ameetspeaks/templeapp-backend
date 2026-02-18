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
