import sys
import os
import asyncio
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.supabase_client import supabase
from app.services.gemini_client import GeminiClient

load_dotenv()

async def enrich_temples():
    print("Starting Temple Enrichment Job...")
    
    # 1. Fetch unenriched temples (Batch size: 20 to avoid rate limits/timeouts)
    try:
        res = supabase.table("temples").select("*").eq("is_ai_enriched", False).limit(20).execute()
        temples = res.data
    except Exception as e:
        print(f"Error fetching temples: {e}")
        return

    if not temples:
        print("No unenriched temples found.")
        return

    print(f"Found {len(temples)} temples to enrich.")
    
    gemini = GeminiClient()
    
    success_count = 0
    
    for temple in temples:
        print(f"Enriching: {temple['name']} ({temple['city']})...")
        
        # 2. Construct Prompt
        # We only ask for fields that are typically missing or need AI generation
        prompt = f"""
        Enrich the database record for this Hindu Temple:
        Name: {temple['name']}
        City: {temple['city']}
        State: {temple['state']}
        Current Deity: {temple.get('deity', 'Unknown')}
        
        Provide a JSON object with the following keys. If information is not available, provide a reasonable best guess based on general knowledge of this temple or similar temples in the region, but keep it factual.
        
        Keys:
        - deity: (String) Main deity if not already correct.
        - timings: (String) Typical opening hours (e.g. "6:00 AM - 12:00 PM, 4:00 PM - 9:00 PM").
        - history: (String) Brief history (approx 100 words).
        - significance: (String) Religious or architectural significance (approx 100 words).
        - darshan_timings: (JSON Array of strings) e.g. ["Morning: 6 AM - 12 PM", "Evening: 4 PM - 9 PM"]
        - puja_timings: (JSON Array of strings) List of daily aartis/pujas.
        - major_festivals: (JSON Array of strings) Top 3-5 festivals celebrated here.
        - how_to_reach: (JSON Object) keys: "by_air", "by_train", "by_road".
        - nearby_attractions: (JSON Array of strings) 3 nearby places to visit.
        - interesting_facts: (JSON Array of strings) 2-3 unique facts.
        - dress_code: (String) typically "Traditional wear recommended" or specific rules.
        - photography_allowed: (Boolean) true/false.
        - entry_fee: (String) e.g. "Free" or amount.
        - best_time_to_visit: (String) e.g. "October to March".
        """
        
        try:
            # 3. Call Gemini
            # Rate limit handling inside loop
            await asyncio.sleep(2) 
            
            ai_data = await gemini.generate_json(prompt, model="flash")
            
            # 4. Prepare Update Payload
            update_data = {
                "deity": ai_data.get("deity", temple.get("deity")),
                "timings": ai_data.get("timings", temple.get("timings", "Not Available")),
                "history": ai_data.get("history"),
                "significance": ai_data.get("significance"),
                "darshan_timings": ai_data.get("darshan_timings"),
                "puja_timings": ai_data.get("puja_timings", []),
                "major_festivals": ai_data.get("major_festivals", []),
                "how_to_reach": ai_data.get("how_to_reach"),
                "nearby_attractions": ai_data.get("nearby_attractions", []),
                "interesting_facts": ai_data.get("interesting_facts", []),
                "dress_code": ai_data.get("dress_code"),
                "photography_allowed": ai_data.get("photography_allowed"),
                "entry_fee": ai_data.get("entry_fee"),
                "best_time_to_visit": ai_data.get("best_time_to_visit"),
                "enriched_at": "now()",
                "is_ai_enriched": True
            }
            
            # 5. Update Database
            supabase.table("temples").update(update_data).eq("id", temple['id']).execute()
            print(f"  - Success.")
            success_count += 1
            
        except Exception as e:
            print(f"  ! Failed to enrich {temple['name']}: {e}")
            
    print(f"Job Completed. Enriched {success_count}/{len(temples)} temples.")

if __name__ == "__main__":
    asyncio.run(enrich_temples())
