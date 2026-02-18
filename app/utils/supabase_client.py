from supabase import create_client, Client
from app.config import settings

def get_supabase_client() -> Client:
    url = settings.SUPABASE_URL
    key = settings.SUPABASE_KEY
    if not url or not key:
        # Fallback for build/test environments without credentials
        return create_client("https://placeholder.supabase.co", "placeholder")
    return create_client(url, key)

supabase = get_supabase_client()
