import sys
import os
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.panchang_engine import PanchangEngine
from app.services.gemini_client import GeminiClient
from app.utils.supabase_client import supabase
import uuid
import json

load_dotenv()

async def enrich_with_ai(date_str, city, panchang_basic):
    """
    Use Gemini to get festival details and descriptions.
    """
    gemini = GeminiClient()
    
    prompt = f"""
    Analyze the Panchang data for {date_str} in {city}: {panchang_basic}.
    
    1. Identify if there are any major Hindu festivals or Vrats on this day.
    2. Provide a short description (Hindi & English) for the day's significance.
    3. Provide a short spiritual message/quote.
    
    Output JSON only:
    {{
        "festivals": [
            {{
                "name": "Festival Name",
                "description": "Short description",
                "type": "Major" | "Minor" | "Jayanti" | "Vrat"
            }}
        ],
        "hindi_description": "2-3 lines in Hindi",
        "english_description": "2-3 lines in English",
        "spiritual_message": "One liner quote"
    }}
    If no festival, "festivals" should be empty list [].
    """
    
    try:
        data = await gemini.generate_json(prompt, model="flash")
        return data
    except Exception as e:
        print(f"  ! AI Enrichment failed: {e}")
        return {}

async def generate_daily_data(start_date_str=None, end_date_str=None, days=10, city="Delhi", batch_size=30):
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else datetime.now().date()
    
    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        days = (end_date - start_date).days + 1
    
    print(f"Starting Panchang Generation for {city}. Start: {start_date}, Days: {days}, Batch Size: {batch_size}")
    
    engine = PanchangEngine()
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        date_str = current_date.strftime("%Y-%m-%d")
        
        print(f"[{i+1}/{days}] Processing {date_str}...")
        
        # 1. Calculate Panchang
        try:
            panchang_data = engine.calculate_panchang(date_str, city)
            
            # 2. AI Enrichment
            ai_data = await enrich_with_ai(date_str, city, panchang_data)
            
            # Merge Data
            full_data = panchang_data.copy()
            if ai_data:
                full_data["hindi_description"] = ai_data.get("hindi_description")
                full_data["english_description"] = ai_data.get("english_description")
                full_data["spiritual_message"] = ai_data.get("spiritual_message")
                
                # Update festivals list in panchang table
                ai_festivals = ai_data.get("festivals", [])
                festival_names = [f["name"] for f in ai_festivals]
                
                # Merge with existing calculated festival if any
                existing_festival = full_data.get("festival")
                if existing_festival and existing_festival not in festival_names:
                    festival_names.insert(0, existing_festival)
                
                full_data["festivals"] = festival_names # Update the list column
                
                # If AI found a festival and we didn't have one, set the main 'festival' field to the first one
                if not full_data.get("festival") and festival_names:
                    full_data["festival"] = festival_names[0]

            # Prepare data for DB (remove internal fields like tithi_index)
            db_payload = full_data.copy()
            if 'tithi_index' in db_payload:
                del db_payload['tithi_index']

            # Upsert Panchang
            # Check existing
            res = supabase.table("panchang_daily").select("id").eq("date", date_str).eq("city", city).execute()
            if res.data:
                # print(f"  - Updating Panchang for {date_str}")
                supabase.table("panchang_daily").update(db_payload).eq("id", res.data[0]['id']).execute()
            else:
                # print(f"  - Inserting Panchang for {date_str}")
                supabase.table("panchang_daily").insert(db_payload).execute()
                
            # 3. Insert Festivals into 'festivals' table
            if ai_data and ai_data.get("festivals"):
                for fest in ai_data["festivals"]:
                    # Check if exists to avoid dupes (rough check by name & date)
                    # We might want a unique constraint or check logic. 
                    # For now, simple check:
                    f_res = supabase.table("festivals").select("id").eq("name", fest["name"]).eq("start_date", date_str).execute()
                    
                    if not f_res.data:
                        f_payload = {
                            "name": fest["name"],
                            "start_date": date_str,
                            "end_date": date_str,
                            "description": fest.get("description"),
                             # "type": fest.get("type") # If schema has type
                        }
                        supabase.table("festivals").insert(f_payload).execute()
                        print(f"  + Inserted Festival: {fest['name']}")
                 
        except Exception as e:
            print(f"  ! Error generating Panchang/Festival: {e}")
            continue

        # 4. Calculate Muhurats
        try:
            muhurats = engine.calculate_muhurats(date_str, city)
            
            # Upsert Muhurats
            # We first delete existing auto-generated ones for this date/city/type to avoid duplicates 
            # or we just insert if not checks. 
            # Strategy: Delete overlap for these specific types on this date/city.
            types_to_remove = ["Abhijit", "Brahma", "Godhuli"]
            supabase.table("muhurats").delete().eq("date", date_str).eq("city", city).in_("type", types_to_remove).execute()
            
            if muhurats:
                # print(f"  - Inserting {len(muhurats)} Muhurats")
                supabase.table("muhurats").insert(muhurats).execute()
                
        except Exception as e:
            print(f"  ! Error generating Muhurats: {e}")
        
        # Batch Handling
        if (i + 1) % batch_size == 0:
            print(f"--- Batch {int((i+1)/batch_size)} Completed ({i+1} days) ---")
            await asyncio.sleep(1)

    print("Generation completed successfully.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Generate Panchang Data')
    parser.add_argument('--days', type=int, default=10, help='Number of days to generate (ignored if end_date provided)')
    parser.add_argument('--start_date', type=str, help='Start date YYYY-MM-DD')
    parser.add_argument('--end_date', type=str, help='End date YYYY-MM-DD (optional)')
    parser.add_argument('--city', type=str, default='Delhi', help='City name')
    parser.add_argument('--batch_size', type=int, default=30, help='Batch size for logging')
    
    args = parser.parse_args()
    
    asyncio.run(generate_daily_data(args.start_date, args.end_date, args.days, args.city, args.batch_size))
