import asyncio
from app.services.audio_pipeline import AudioPipeline
from app.models.schemas import AartiFetchAudioRequest

async def verify_aarti_pipeline():
    print("Starting verification of Aarti Pipeline...")
    pipeline = AudioPipeline()
    
    # Test Data
    aarti_title = "Om Jai Jagdish Hare"
    deity = "Vishnu"
    aarti_id = "test_verification_001"
    
    print(f"Fetching audio for: {aarti_title} ({deity})")
    
    try:
        # 1. Fetch using Supabase Storage (Default)
        result = pipeline.search_and_fetch_audio(aarti_title, deity, aarti_id, provider="SUPABASE")
        print("\n[SUCCESS] Fetched with Supabase Provider:")
        print(f"Audio URL: {result['audio_url']}")
        print(f"Duration: {result['duration_seconds']}s")
        print(f"Storage Provider: {result['storage_provider']}")
        
        if "supabase" not in result['audio_url'] and "127.0.0.1" not in result['audio_url'] and "localhost" not in result['audio_url']:
             print("[WARNING] URL does not look like a Supabase URL, but might be proxied or custom domain.")

    except Exception as e:
        print(f"\n[ERROR] Verification failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify_aarti_pipeline())
