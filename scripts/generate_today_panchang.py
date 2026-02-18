
import sys
import os
import asyncio
from datetime import datetime
import pytz

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.panchang_calculator import PanchangCalculator
from app.services.gemini_client import GeminiClient
from app.utils.supabase_client import supabase

async def generate_panchang_today():
    try:
        print("Starting Panchang Generation for Today...")
        
        # 1. Get Today's Date (IST)
        ist = pytz.timezone('Asia/Kolkata')
        today = datetime.now(ist).strftime("%Y-%m-%d")
        city = "Delhi"
        
        print(f"Date: {today}, City: {city}")
        
        # 2. Calculate
        calculator = PanchangCalculator()
        calc_data = calculator.calculate(today, city)
        print("Calculation complete.")
        
        # 3. AI Enrich
        gemini = GeminiClient()
        prompt = f"""
        Generate a daily panchang description based on this data: {calc_data}.
        Include any major Hindu festival falling on this tithi/date if applicable.
        
        Output JSON:
        {{
            "hindi_description": "120 words devotional Pandit style with blessings",
            "english_description": "120 words explanation",
            "spiritual_message": "2 sentences quote or wisdom",
            "festivals": ["List of festivals if any, else empty"]
        }}
        """
        
        print("Requesting AI enrichment (Gemini)...")
        ai_data = await gemini.generate_json(prompt, model="flash") # Using flash (gemini-pro fallback)
        print("AI enrichment complete.")
        
        # 4. Save
        full_data = {**calc_data, **ai_data}
        
        # Check if exists
        print("Saving to Supabase...")
        res = supabase.table("panchang_daily").select("id").eq("date", today).eq("city", city).execute()
        
        if res.data:
            supabase.table("panchang_daily").update(full_data).eq("id", res.data[0]['id']).execute()
            print("Updated existing record.")
        else:
            supabase.table("panchang_daily").insert(full_data).execute()
            print("Inserted new record.")
            
        print("SUCCESS: Panchang generated and saved.")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(generate_panchang_today())
