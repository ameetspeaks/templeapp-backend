from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any, Union
from datetime import date, datetime
from enum import Enum

# --- Shared ---
class SuccessResponse(BaseModel):
    status: str = "ok" # Changed from success: bool to status: "ok"|"error" to match spec
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    status: str = "error"
    error: Dict[str, Any]

class PaginationResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: List[Any]

# --- Enums ---
class Deity(str, Enum):
    GANESH = "Ganesh"
    SHIVA = "Shiva"
    VISHNU = "Vishnu"
    KRISHNA = "Krishna"
    RAM = "Ram"
    HANUMAN = "Hanuman"
    DURGA = "Durga"
    LAKSHMI = "Lakshmi"
    SARASWATI = "Saraswati"
    KALI = "Kali"
    OTHER = "Other"

# --- Temple ---
class TimeSlot(BaseModel):
    label: str
    start: str # HH:MM
    end: str # HH:MM

class TempleBase(BaseModel):
    name: str
    deity: str
    latitude: float
    longitude: float
    address: Optional[str] = None
    city: str
    state: str
    contact: Optional[str] = None
    description: Optional[str] = None
    image_urls: Optional[List[str]] = []
    darshan_times: Optional[List[TimeSlot]] = []
    puja_times: Optional[List[TimeSlot]] = []

class Temple(TempleBase):
    id: str
    status: Optional[str] = None # pending/enriched

class TempleAddRequest(TempleBase):
    pass

class TempleEnrichRequest(BaseModel):
    temple_id: str

class TempleBulkEnrichRequest(BaseModel):
    limit: int = 10

# --- Panchang & Calendar ---
class PanchangData(BaseModel):
    date: str
    tithi: str
    nakshatra: str
    yoga: str
    karan: str
    sunrise: str
    sunset: str
    moonrise: Optional[str] = None
    rahukaal: Optional[str] = None
    special_festival: Optional[str] = None

class Festival(BaseModel):
    id: str
    name: str
    start_date: str
    end_date: Optional[str] = None
    description: Optional[str] = None
    icon_url: Optional[str] = None

class Muhurat(BaseModel):
    id: str
    type: str # vivah, griha_pravesh, etc.
    start: str # ISO
    end: str # ISO
    city: str
    description: Optional[str] = None

# --- Aarti & Bhajan ---
class Lyrics(BaseModel):
    hi: Optional[str] = None
    en: Optional[str] = None # transliteration or meaning depending on context, keeping simple map for now

class Aarti(BaseModel):
    id: str
    title: str
    deity: str
    audio_url: Optional[str] = None
    duration_sec: Optional[int] = None
    lyrics: Optional[Lyrics] = None

class Bhajan(BaseModel):
    id: str
    title: str
    singer: Optional[str] = None
    audio_url: Optional[str] = None
    duration_sec: Optional[int] = None
    lyrics: Optional[Lyrics] = None
    category: Optional[str] = None
    deity: Optional[str] = None
    image_url: Optional[str] = None

# --- Puja Guide ---
class PujaSamagri(BaseModel):
    name: str
    qty: Optional[str] = None
    is_optional: bool = False

class PujaStep(BaseModel):
    index: int
    text: str
    audio_url: Optional[str] = None
    image_url: Optional[str] = None

class PujaGuide(BaseModel):
    id: str
    title: str
    category: str
    samagri: List[PujaSamagri]
    steps: List[PujaStep]
    image_urls: Optional[List[str]] = None

# --- Home ---
class HomeSummary(BaseModel):
    greeting: str
    panchang: PanchangData
    featured_festivals: List[Festival]
    quick_counts: Dict[str, int]

# --- Search ---
class SearchResult(BaseModel):
    type: str # temple, aarti, bhajan, puja, festival
    id: str
    title: str
    subtitle: Optional[str] = None
    image_url: Optional[str] = None

# --- Config ---
class AppConfig(BaseModel):
    languages: List[str]
    features: Dict[str, bool]
    min_version: str

# --- User & Auth ---
class UserProfile(BaseModel):
    id: str
    name: Optional[str] = None
    city: Optional[str] = None
    language: Optional[str] = None
    favorites: Optional[Dict[str, List[str]]] = None # { "temples": ["id1"], ... }

# --- Request Models for Routers ---
class SearchRequest(BaseModel):
    q: str
    page: int = 1
    page_size: int = 20

class GeoRequest(BaseModel):
    lat: float
    lng: float
    radius_km: float = 10.0

class RegisterPushRequest(BaseModel):
    device_id: str
    token: str
    platform: str
    city: Optional[str] = None
    tz: Optional[str] = None

class BlogGenerateRequest(BaseModel):
    keyword_id: Optional[str] = None
    category: Optional[str] = None

class BlogBatchRequest(BaseModel):
    count: int = 1

