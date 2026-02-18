import sys
import os
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.panchang_engine import PanchangEngine
from app.utils.supabase_client import supabase

load_dotenv()

async def generate_daily_data(start_date_str=None, days=10, city="Delhi"):
    print(f"Starting Panchang Generation for {city} from {start_date_str or 'Today'} for {days} days...")
    
    engine = PanchangEngine()
    
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else datetime.now().date()
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        date_str = current_date.strftime("%Y-%m-%d")
        
        print(f"Processing {date_str}...")
        
        # 1. Calculate Panchang
        try:
            panchang_data = engine.calculate_panchang(date_str, city)
            
            # Upsert Panchang
            # Check existing
            res = supabase.table("panchang_daily").select("id").eq("date", date_str).eq("city", city).execute()
            if res.data:
                print(f"  - Updating Panchang for {date_str}")
                supabase.table("panchang_daily").update(panchang_data).eq("id", res.data[0]['id']).execute()
            else:
                 print(f"  - Inserting Panchang for {date_str}")
                 supabase.table("panchang_daily").insert(panchang_data).execute()
                 
        except Exception as e:
            print(f"  ! Error generating Panchang: {e}")
            continue

        # 2. Calculate Muhurats
        try:
            muhurats = engine.calculate_muhurats(date_str, city)
            
            # Upsert Muhurats
            # We first delete existing auto-generated ones for this date/city/type to avoid duplicates 
            # or we just insert if not checks. 
            # Strategy: Delete overlap for these specific types on this date/city.
            types_to_remove = ["Abhijit", "Brahma", "Godhuli"]
            supabase.table("muhurats").delete().eq("date", date_str).eq("city", city).in_("type", types_to_remove).execute()
            
            if muhurats:
                print(f"  - Inserting {len(muhurats)} Muhurats")
                supabase.table("muhurats").insert(muhurats).execute()
                
        except Exception as e:
            print(f"  ! Error generating Muhurats: {e}")

    print("Batch generation completed.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Generate Panchang Data')
    parser.add_argument('--days', type=int, default=10, help='Number of days to generate')
    parser.add_argument('--start_date', type=str, help='Start date YYYY-MM-DD')
    parser.add_argument('--city', type=str, default='Delhi', help='City name')
    
    args = parser.parse_args()
    
    asyncio.run(generate_daily_data(args.start_date, args.days, args.city))
