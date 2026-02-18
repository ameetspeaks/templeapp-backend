import cloudinary
import cloudinary.uploader
import cloudinary.api
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger("cloudinary_service")

class CloudinaryService:
    def __init__(self):
        if not settings.CLOUDINARY_CLOUD_NAME:
            logger.warning("Cloudinary credentials not set")
            # Don't return, let it fail if used, or handle gracefully
        else:
            cloudinary.config(
                cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                api_key=settings.CLOUDINARY_API_KEY,
                api_secret=settings.CLOUDINARY_API_SECRET
            )

    def upload_audio(self, file_path: str, public_id: str, folder: str = "templeapp/aartis") -> str:
        try:
            # Resource type 'video' is used for audio in Cloudinary
            response = cloudinary.uploader.upload(
                file_path,
                resource_type="video", 
                public_id=public_id,
                folder=folder,
                overwrite=True
            )
            return response.get("secure_url")
        except Exception as e:
            logger.error(f"Cloudinary upload failed: {e}")
            raise

    def upload_from_url(self, source_url: str, public_id: str, folder: str = "templeapp/aartis") -> str:
        try:
            response = cloudinary.uploader.upload(
                source_url,
                resource_type="video",
                public_id=public_id,
                folder=folder,
                overwrite=True
            )
            return response.get("secure_url")
        except Exception as e:
            logger.error(f"Cloudinary upload from URL failed: {e}")
            raise

    def delete_audio(self, public_id: str) -> bool:
        try:
            cloudinary.uploader.destroy(public_id, resource_type="video")
            return True
        except Exception as e:
            logger.error(f"Cloudinary delete failed: {e}")
            return False

    def get_audio_info(self, public_id: str) -> dict:
        try:
            resource = cloudinary.api.resource(public_id, resource_type="video")
            return {
                "size": resource.get("bytes"),
                "duration": resource.get("duration"),
                "format": resource.get("format"),
                "url": resource.get("secure_url")
            }
        except Exception as e:
            logger.error(f"Cloudinary info failed: {e}")
            return {}
