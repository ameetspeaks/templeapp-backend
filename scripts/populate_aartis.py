import asyncio
import os
import sys
# Ensure backend is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.gemini_client import GeminiClient
from app.services.audio_pipeline import AudioPipeline
from app.utils.supabase_client import supabase
from app.utils.logger import setup_logger

logger = setup_logger("populate_aartis")

async def main():
    gemini = GeminiClient()
    pipeline = AudioPipeline()
    
    logger.info("Starting Aarti Population Script")
    
    # 1. Ask Gemini for a list of 10 Aartis
    prompt = """
    Generate a JSON list of 10 popular Hindu Aartis.
    Fields: title, deity, aarti_type (morning/evening/festival).
    Include diverse deities (Ganesh, Vishnu, Shiva, Durga, Lakshmi, Krishna, Rama, Hanuman, Sai Baba, etc.)
    and popular variations.
    Example: [{"title": "Om Jai Jagdish Hare", "deity": "Vishnu", "aarti_type": "evening"}]
    """
    
    try:
        logger.info("Generating Aarti list from Gemini...")
        aarti_list = await gemini.generate_json(prompt, model="flash")
        logger.info(f"Generated {len(aarti_list)} Aartis")
    except Exception as e:
        logger.error(f"Failed to generate list: {e}")
        return

    # 2. Process each Aarti
    for i, item in enumerate(aarti_list):
        title = item.get("title")
        deity = item.get("deity")
        aarti_type = item.get("aarti_type", "general")
        
        logger.info(f"[{i+1}/{len(aarti_list)}] Processing: {title} ({deity})")
        
        try:
            # Check if exists
            res = supabase.table("aartis").select("id").eq("title", title).eq("deity", deity).execute()
            if res.data:
                logger.info(" - Already exists, skipping.")
                continue

            # Generate Lyrics & Metadata
            lyrics_prompt = f"""
            Generate authentic lyrics for {title} aarti of {deity}. Type: {aarti_type}.
            Output JSON: lyrics_hindi, lyrics_english_transliteration, lyrics_english_meaning, significance, best_time, estimated_duration_minutes.
            """
            
            # Use 'flash' for speed, 'pro' for quality. Flash is fine for lyrics usually.
            ai_data = await gemini.generate_json(lyrics_prompt, model="flash")
            
            # Fix: Gemini might return a list [dict] or just dict
            if isinstance(ai_data, list):
                if ai_data:
                    ai_data = ai_data[0]
                else:
                    logger.error(" - Empty list returned from Gemini")
                    continue
            
            if not isinstance(ai_data, dict):
                logger.error(f" - Invalid AI data format: {type(ai_data)}")
                continue
            
            db_data = {
                "title": title,
                "deity": deity,
                "aarti_type": aarti_type,
                "language": "Hindi",
                **ai_data,
                "status": "pending_audio",
                "storage_provider": "SUPABASE",
                "created_at": "now()"
            }
            
            # Insert into DB
            insert_res = supabase.table("aartis").insert(db_data).execute()
            if not insert_res.data:
                logger.error(" - Failed to insert record")
                continue
                
            aarti_id = insert_res.data[0]['id']
            logger.info(f" - Created record ID: {aarti_id}")
            
            # Fetch Audio
            logger.info(" - Fetching audio...")
            audio_res = pipeline.search_and_fetch_audio(title, deity, aarti_id, provider="SUPABASE")
            
            # Update DB with Audio
            update_data = {
                "audio_url": audio_res['audio_url'],
                "audio_source_url": audio_res['source_url'],
                "duration_seconds": audio_res['duration_seconds'],
                "status": "complete"
            }
            supabase.table("aartis").update(update_data).eq("id", aarti_id).execute()
            logger.info(" - Audio fetched and saved.")
            
        except Exception as e:
            logger.error(f" - Failed to process {title}: {e}")
            await asyncio.sleep(1) # Backoff slightly
            
    logger.info("Batch Population Completed")

if __name__ == "__main__":
    asyncio.run(main())
