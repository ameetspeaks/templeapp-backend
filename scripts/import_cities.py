import sys
import os
import json
import asyncio
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.supabase_client import supabase

load_dotenv()

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "indian_cities.json")

async def import_cities():
    if not os.path.exists(DATA_FILE):
        print(f"Error: Data file not found at {DATA_FILE}")
        return

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    print(f"Loaded data for {len(data)} states.")

    total_added = 0
    total_skipped = 0

    for state, cities in data.items():
        print(f"Processing {state} ({len(cities)} cities)...")
        
        # Prepare batch for speed (though Supabase REST uses single inserts/upserts usually)
        # We'll do one by one to handle conflicts gracefully or use upsert
        
        payloads = []
        for city in cities:
            payloads.append({
                "city": city,
                "state": state,
                "status": "pending",
                "temple_count": 0
            })
            
        # Bulk upsert per state
        try:
            # Upsert on conflict (city, state) DO NOTHING is not directly available in py-supabase easily without 'ignore_duplicates' or manual check
            # But upsert works. We just don't want to reset status if it's already 'completed'.
            # So checking existing is safer.
            
            # Fetch existing for this state
            res = supabase.table("locations").select("city").eq("state", state).execute()
            existing_cities = {item['city'] for item in res.data}
            
            new_cities_payload = [p for p in payloads if p['city'] not in existing_cities]
            
            if new_cities_payload:
                res = supabase.table("locations").insert(new_cities_payload).execute()
                print(f"  + Added {len(new_cities_payload)} new cities in {state}")
                total_added += len(new_cities_payload)
            else:
                print(f"  - No new cities to add in {state}")
                
            total_skipped += len(payloads) - len(new_cities_payload)

        except Exception as e:
            print(f"Error processing {state}: {e}")

    print(f"\nImport Completed.")
    print(f"Total Added: {total_added}")
    print(f"Total Skipped (Already Exists): {total_skipped}")

if __name__ == "__main__":
    asyncio.run(import_cities())
