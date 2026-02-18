import os
import glob
import tempfile
import yt_dlp
from app.services.cloudinary_service import CloudinaryService
from app.services.supabase_storage_service import SupabaseStorageService
from app.utils.logger import setup_logger

logger = setup_logger("audio_pipeline")

class AudioPipeline:
    def __init__(self):
        self.cloudinary = CloudinaryService()
        self.supabase_storage = SupabaseStorageService()

    def search_and_fetch_audio(self, aarti_title: str, deity: str, aarti_id: str, provider: str = "SUPABASE") -> dict:
        query = f"{aarti_title} {deity} aarti original"
        logger.info(f"Searching for: {query} with provider {provider}")
        
        # Temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': os.path.join(temp_dir, '%(id)s.%(ext)s'),
                'noplaylist': True,
                'quiet': True,
                'max_filesize': 50 * 1024 * 1024, # 50MB
                'nocheckcertificate': True,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'ios']
                    }
                }
            }
            
            # Check for cookies.txt in current or parent directory
            cookies_path = "cookies.txt"
            if not os.path.exists(cookies_path):
                # Try backend/cookies.txt
                cookies_path = os.path.join("backend", "cookies.txt")
            
            if os.path.exists(cookies_path):
                logger.info(f"Using cookies from {cookies_path}")
                ydl_opts['cookiefile'] = cookies_path
            else:
                logger.warning("No cookies.txt found. YouTube fetch might fail.")
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Search and download first result
                    # "ytsearch1:" downloads the first result of search
                    info = ydl.extract_info(f"ytsearch1:{query}", download=True)
                    
                    if 'entries' in info:
                        video_info = info['entries'][0]
                    else:
                        video_info = info

                    # Find the downloaded file
                    files = glob.glob(os.path.join(temp_dir, "*.mp3"))
                    if not files:
                        raise Exception("Download failed, no file found")
                        
                    file_path = files[0]
                    source_url = video_info.get('webpage_url')
                    duration = video_info.get('duration')
                    
                    # Sanitize deity name for folder
                    safe_deity = "".join(c for c in deity if c.isalnum()).lower()
                    
                    secure_url = ""
                    
                    if provider == "CLOUDINARY":
                        public_id = f"aarti_{aarti_id}"
                        folder = f"templeapp/aartis/{safe_deity}"
                        logger.info(f"Uploading to Cloudinary: {public_id}")
                        secure_url = self.cloudinary.upload_audio(file_path, public_id, folder)
                    else:
                        # Supabase Storage
                        filename = f"{aarti_id}.mp3"
                        destination = f"{safe_deity}/{filename}"
                        logger.info(f"Uploading to Supabase: {destination}")
                        secure_url = self.supabase_storage.upload_file(file_path, destination)
                    
                    return {
                        "audio_url": secure_url,
                        "source_url": source_url,
                        "duration_seconds": duration,
                        "file_size_mb": os.path.getsize(file_path) / (1024 * 1024),
                        "quality": "192kbps",
                        "storage_provider": provider
                    }
                    
            except Exception as e:
                logger.error(f"Audio pipeline failed: {e}")
                raise

    def fetch_from_direct_url(self, url: str, aarti_id: str, deity: str, provider: str = "SUPABASE") -> dict:
         with tempfile.TemporaryDirectory() as temp_dir:
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': os.path.join(temp_dir, '%(id)s.%(ext)s'),
                'noplaylist': True,
                'quiet': True,
                'max_filesize': 50 * 1024 * 1024,
            }
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    
                    files = glob.glob(os.path.join(temp_dir, "*.mp3"))
                    if not files:
                        raise Exception("Download failed")
                        
                    file_path = files[0]
                    duration = info.get('duration')
                    
                    safe_deity = "".join(c for c in deity if c.isalnum()).lower()
                    
                    secure_url = ""
                    
                    if provider == "CLOUDINARY":
                        public_id = f"aarti_{aarti_id}"
                        folder = f"templeapp/aartis/{safe_deity}"
                        secure_url = self.cloudinary.upload_audio(file_path, public_id, folder)
                    else:
                         # Supabase Storage
                        filename = f"{aarti_id}.mp3"
                        destination = f"{safe_deity}/{filename}"
                        secure_url = self.supabase_storage.upload_file(file_path, destination)

                    return {
                        "audio_url": secure_url,
                        "source_url": url,
                        "duration_seconds": duration,
                        "file_size_mb": os.path.getsize(file_path) / (1024 * 1024),
                        "quality": "192kbps",
                        "storage_provider": provider
                    }
            except Exception as e:
                logger.error(f"Direct fetch failed: {e}")
                raise
