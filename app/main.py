from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.routers import panchang, blogs, temples, muhurat, aarti, jobs
from app.services.scheduler_service import start_scheduler, stop_scheduler, scheduler
from app.utils.response import error_response
from app.jobs_definitions import (
    job_generate_blogs, 
    job_enrich_temples,
    job_generate_aarti_lyrics,
    job_fetch_aarti_audio
)
import logging

# Configure root logger
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="TempleApp AI Backend", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return error_response(str(exc), 500)

@app.on_event("startup")
async def startup_event():
    start_scheduler()
    
    # Register Jobs (IST times)
    # Note: Server time might be UTC. APScheduler handles timezone if pytz provided.
    # Assuming container runs in UTC, we need to adjust or use timezone arg.
    
    # Add jobs but pause immediately to allow manual triggering only
    scheduler.add_job(job_generate_blogs, 'cron', hour=6, minute=0, timezone='Asia/Kolkata', id="blog_daily").pause()
    scheduler.add_job(job_enrich_temples, 'cron', hour=7, minute=0, timezone='Asia/Kolkata', id="temple_enrich").pause()
    scheduler.add_job(job_generate_aarti_lyrics, 'cron', hour=9, minute=0, timezone='Asia/Kolkata', id="aarti_lyrics").pause()
    scheduler.add_job(job_fetch_aarti_audio, 'cron', hour=10, minute=0, timezone='Asia/Kolkata', id="aarti_audio").pause()

@app.on_event("shutdown")
async def shutdown_event():
    stop_scheduler()

# Include Routers
app.include_router(panchang.router)
app.include_router(blogs.router)
app.include_router(temples.router)
app.include_router(muhurat.router)
app.include_router(aarti.router)
app.include_router(jobs.router)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "uptime_seconds": 0, # Placeholder
        "models": {
            "flash": "gemini-2.0-flash-exp",
            "pro": "gemini-1.5-pro"
        }
    }
