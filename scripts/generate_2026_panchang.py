
import sys
import os
import asyncio
from datetime import datetime, timedelta
import pytz
import logging

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.panchang_calculator import PanchangCalculator
from app.services.gemini_client import GeminiClient
from app.utils.supabase_client import supabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def generate_panchang_2026():
    start_date = datetime(2026, 1, 1)
    end_date = datetime(2026, 12, 31)
    city = "Delhi"
    
    calculator = PanchangCalculator()
    gemini = GeminiClient()
    
    current_date = start_date
    delta = timedelta(days=1)
    
    success_count = 0
    fail_count = 0
    
    print(f"Starting Bulk Generation for 2026 ({start_date.date()} to {end_date.date()}) in {city}...")
    
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")
        
        try:
            logger.info(f"Processing {date_str}...")
            
            # 1. Base Calculation (Local Ephem + External API attempt)
            # This uses the hybrid calculator we built.
            calc_data = calculator.calculate(date_str, city)
            
            # 2. AI Enrichment (Descriptions)
            # We need this for hindi_description, english_description, spiritual_message
            prompt = f"""
            Generate a daily panchang description for {date_str} ({city}) based on this data: {calc_data}.
            Include major Hindu festivals for this specific tithi/date.
            
            Output JSON with these specific keys:
            {{
                "hindi_description": "150 words devotional Pandit style with blessings",
                "english_description": "150 words explanation",
                "spiritual_message": "2 sentences Vedic wisdom quote",
                "festivals": ["List of festivals if any, e.g. 'Diwali', 'None'"],
                "vrat": "Any fast observed today (e.g. 'Ekadashi Vrat')"
            }}
            """
            
            # Use 'flash' model (mapped to gemini-1.5-flash via REST)
            # Rate limit handling: Sleep a bit to avoid hitting 15 RPM limits if using free tier heavily
            await asyncio.sleep(4) 
            
            ai_data = await gemini.generate_json(prompt, model="flash")
            
            # 3. Merge & Save
            full_data = {**calc_data, **ai_data}
            
            # Validate festivals is a list
            if not isinstance(full_data.get('festivals'), list):
                if isinstance(full_data.get('festivals'), str):
                     full_data['festivals'] = [full_data['festivals']]
                else:
                     full_data['festivals'] = []
            
            # Upsert to Supabase
            res = supabase.table("panchang_daily").select("id").eq("date", date_str).eq("city", city).execute()
            
            if res.data:
                supabase.table("panchang_daily").update(full_data).eq("id", res.data[0]['id']).execute()
                logger.info(f"Updated: {date_str}")
            else:
                supabase.table("panchang_daily").insert(full_data).execute()
                logger.info(f"Inserted: {date_str}")
                
            success_count += 1
            
        except Exception as e:
            logger.error(f"Failed {date_str}: {e}")
            fail_count += 1
            # Continue to next day even if failed
            
        current_date += delta
        
    print(f"COMPLETED. Success: {success_count}, Failed: {fail_count}")

if __name__ == "__main__":
    asyncio.run(generate_panchang_2026())
