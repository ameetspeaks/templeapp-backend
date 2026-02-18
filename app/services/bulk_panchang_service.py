
import asyncio
from datetime import datetime, timedelta
import logging
from app.services.panchang_calculator import PanchangCalculator
from app.services.gemini_client import GeminiClient
from app.utils.supabase_client import supabase

logger = logging.getLogger(__name__)

class BulkPanchangService:
    def __init__(self):
        self.calculator = PanchangCalculator()
        self.gemini = GeminiClient()

    async def generate_2026(self, city: str = "Delhi"):
        start_date = datetime(2026, 1, 1)
        end_date = datetime(2026, 12, 31)
        
        # Use self instances
        # calculator = PanchangCalculator() -> self.calculator
        # gemini = GeminiClient() -> self.gemini
        
        current_date = start_date
        delta = timedelta(days=1)
        
        success_count = 0
        fail_count = 0
        
        logger.info(f"Starting Bulk Generation for 2026 ({start_date.date()} to {end_date.date()}) in {city}...")
        
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            
            try:
                # 1. Base Calculation
                calc_data = self.calculator.calculate(date_str, city)
                
                # 2. AI Enrichment
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
                
                # Rate limit handling
                await asyncio.sleep(2) 
                
                ai_data = await self.gemini.generate_json(prompt, model="flash")
                
                # 3. Merge & Save
                full_data = {**calc_data, **ai_data}
                
                if not isinstance(full_data.get('festivals'), list):
                    if isinstance(full_data.get('festivals'), str):
                         full_data['festivals'] = [full_data['festivals']]
                    else:
                         full_data['festivals'] = []
                
                # Upsert to Supabase
                res = supabase.table("panchang_daily").select("id").eq("date", date_str).eq("city", city).execute()
                
                if res.data:
                    supabase.table("panchang_daily").update(full_data).eq("id", res.data[0]['id']).execute()
                else:
                    supabase.table("panchang_daily").insert(full_data).execute()
                    
                success_count += 1
                logger.info(f"Generated {date_str}")
                
            except Exception as e:
                logger.error(f"Failed {date_str}: {e}")
                fail_count += 1
                
            current_date += delta
            
        logger.info(f"COMPLETED 2026 Bulk. Success: {success_count}, Failed: {fail_count}")
