from fastapi import Header, HTTPException, Security
from app.config import settings

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.ADMIN_API_KEY:
        # We raise HTTPException here, but we'll handle the format in main.py exception handler
        # to ensure it returns the {success: false, ...} format
        raise HTTPException(status_code=401, detail="Unauthorized")
    return x_api_key
