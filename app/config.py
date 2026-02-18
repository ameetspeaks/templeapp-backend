import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    UPSTASH_REDIS_URL = os.getenv("UPSTASH_REDIS_URL")
    UPSTASH_REDIS_TOKEN = os.getenv("UPSTASH_REDIS_TOKEN")
    ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")

settings = Settings()
