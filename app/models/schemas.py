from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date, datetime

# --- Shared ---
class SuccessResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    message: str
    timestamp: datetime

# --- Panchang ---
class PanchangRequest(BaseModel):
    date: str = Field(..., description="YYYY-MM-DD")
    city: str = Field(..., description="City name")

class PanchangRangeRequest(BaseModel):
    start_date: str
    end_date: str
    city: str

class PanchangData(BaseModel):
    date: str
    city: str
    sunrise: str
    sunset: str
    moonrise: str
    tithi: str
    paksha: str
    nakshatra: str
    yoga: str
    karan: str
    rahukaal: str
    yamaganda: Optional[str] = None
    gulika: Optional[str] = None
    hindi_description: Optional[str] = None
    english_description: Optional[str] = None
    spiritual_message: Optional[str] = None
    festivals: Optional[List[str]] = None

# --- Blog ---
class BlogGenerateRequest(BaseModel):
    keyword_id: Optional[str] = None
    category: Optional[str] = None

class BlogBatchRequest(BaseModel):
    count: int = 5

class BlogResponse(BaseModel):
    id: str
    title: str
    slug: str
    status: str
    created_at: str

# --- Temple ---
class TempleAddRequest(BaseModel):
    name: str
    deity: str
    city: str
    state: str
    address: Optional[str] = None
    contact: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class TempleEnrichRequest(BaseModel):
    temple_id: str

class TempleBulkEnrichRequest(BaseModel):
    limit: int = 10

# --- Muhurat ---
class MuhuratCalculateRequest(BaseModel):
    muhurat_type: str
    month: int
    year: int
    city: str

class MuhuratMonthlyReportRequest(BaseModel):
    month: int
    year: int
    city: str

class MuhuratItem(BaseModel):
    date: str
    start_time: str
    end_time: str
    score: float
    reasoning: str

# --- Aarti ---
class AartiGenerateRequest(BaseModel):
    title: str
    deity: str
    aarti_type: str # morning/evening/festival
    language: str = "Hindi"

class AartiBatchGenerateRequest(BaseModel):
    items: List[AartiGenerateRequest]

class AartiFetchAudioRequest(BaseModel):
    aarti_id: str

class AartiFetchAudioUrlRequest(BaseModel):
    source_url: str

class AartiFetchAudioBatchRequest(BaseModel):
    limit: int = 5

# --- Job ---
class JobTriggerRequest(BaseModel):
    job_name: str
