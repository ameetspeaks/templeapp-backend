from fastapi import APIRouter, Depends
from app.models.schemas import SuccessResponse, AppConfig
from app.utils.response import success_response, error_response
from app.utils.auth import verify_api_key
from app.config import settings

router = APIRouter(prefix="/v1/config", tags=["Config V1"])

@router.get("/app", response_model=SuccessResponse)
async def get_app_config(api_key: str = Depends(verify_api_key)):
    try:
        config = {
            "languages": ["en", "hi"],
            "features": {
                "bhajan": True,
                "donations": False,
                "stories": False
            },
            "min_version": "1.0.0"
        }
        return success_response(config)
    except Exception as e:
        return error_response(str(e), 500)
