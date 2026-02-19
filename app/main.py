from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.routers import (
    panchang, blogs, temples, muhurat, aarti, jobs,
    home, bhajan, puja, search, notifications, config, auth
)
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
    pass

@app.on_event("shutdown")
async def shutdown_event():
    stop_scheduler()

# Include Routers
# V1 Routers
app.include_router(home.router)
app.include_router(temples.router)
app.include_router(aarti.router)
app.include_router(bhajan.router)
app.include_router(panchang.router)
app.include_router(panchang.festivals_router) # Exported from panchang.py
app.include_router(muhurat.router)
app.include_router(puja.router)
app.include_router(search.router)
app.include_router(notifications.router)
app.include_router(config.router)
app.include_router(auth.router)

# Legacy/Admin Routers (keeping them if needed, or migration needed if paths conflict)
# Note: routers like 'jobs' and 'blogs' are admin/backend specific, keeping them.
app.include_router(jobs.router)
app.include_router(blogs.router)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "uptime_seconds": 0, # Placeholder
        "models": {
            "flash": "gemini-2.0-flash",
            "pro": "gemini-1.5-pro"
        }
    }

