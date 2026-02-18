import os
from app.utils.supabase_client import supabase
from app.utils.logger import setup_logger
from app.config import settings

logger = setup_logger("supabase_storage_service")

class SupabaseStorageService:
    def __init__(self):
        self.bucket = "aartis"

    def upload_file(self, file_path: str, destination_path: str) -> str:
        """
        Uploads a file to Supabase Storage.
        Returns the public URL of the uploaded file.
        """
        try:
            with open(file_path, 'rb') as f:
                res = supabase.storage.from_(self.bucket).upload(
                    path=destination_path,
                    file=f,
                    file_options={"content-type": "audio/mpeg", "upsert": "true"}
                )
            
            # Construct public URL
            # The client doesn't always return the full URL in the upload response
            public_url_res = supabase.storage.from_(self.bucket).get_public_url(destination_path)
            return public_url_res
        except Exception as e:
            logger.error(f"Supabase storage upload failed: {e}")
            raise

    def delete_file(self, path: str) -> bool:
        try:
            supabase.storage.from_(self.bucket).remove([path])
            return True
        except Exception as e:
            logger.error(f"Supabase storage delete failed: {e}")
            return False

    def list_files(self, path: str = ""):
        try:
            res = supabase.storage.from_(self.bucket).list(path)
            return res
        except Exception as e:
            logger.error(f"Supabase storage list failed: {e}")
            return []
