import sys
import os
import asyncio
from dotenv import load_dotenv

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.supabase_client import supabase

load_dotenv()

# List of major Indian cities/states to seed
# This is a starting list. You can add more.
CITIES = [
    {"city": "Varanasi", "state": "Uttar Pradesh"},
    {"city": "Ayodhya", "state": "Uttar Pradesh"},
    {"city": "Mathura", "state": "Uttar Pradesh"},
    {"city": "Prayagraj", "state": "Uttar Pradesh"},
    {"city": "Haridwar", "state": "Uttarakhand"},
    {"city": "Rishikesh", "state": "Uttarakhand"},
    {"city": "Badrinath", "state": "Uttarakhand"},
    {"city": "Kedarnath", "state": "Uttarakhand"},
    {"city": "Delhi", "state": "Delhi"},
    {"city": "Jaipur", "state": "Rajasthan"},
    {"city": "Udaipur", "state": "Rajasthan"},
    {"city": "Pushkar", "state": "Rajasthan"},
    {"city": "Ujjain", "state": "Madhya Pradesh"},
    {"city": "Omkareshwar", "state": "Madhya Pradesh"},
    {"city": "Indore", "state": "Madhya Pradesh"},
    {"city": "Mumbai", "state": "Maharashtra"},
    {"city": "Pune", "state": "Maharashtra"},
    {"city": "Nashik", "state": "Maharashtra"},
    {"city": "Shirdi", "state": "Maharashtra"},
    {"city": "Pandharpur", "state": "Maharashtra"},
    {"city": "Tirupati", "state": "Andhra Pradesh"},
    {"city": "Vijayawada", "state": "Andhra Pradesh"},
    {"city": "Visakhapatnam", "state": "Andhra Pradesh"},
    {"city": "Srisailam", "state": "Andhra Pradesh"},
    {"city": "Chennai", "state": "Tamil Nadu"},
    {"city": "Madurai", "state": "Tamil Nadu"},
    {"city": "Rameswaram", "state": "Tamil Nadu"},
    {"city": "Kanchipuram", "state": "Tamil Nadu"},
    {"city": "Thanjavur", "state": "Tamil Nadu"},
    {"city": "Kanyakumari", "state": "Tamil Nadu"},
    {"city": "Bangalore", "state": "Karnataka"},
    {"city": "Mysore", "state": "Karnataka"},
    {"city": "Hampi", "state": "Karnataka"},
    {"city": "Gokarna", "state": "Karnataka"},
    {"city": "Udupi", "state": "Karnataka"},
    {"city": "Puri", "state": "Odisha"},
    {"city": "Bhubaneswar", "state": "Odisha"},
    {"city": "Konark", "state": "Odisha"},
    {"city": "Kolkata", "state": "West Bengal"},
    {"city": "Guwahati", "state": "Assam"},
    {"city": "Amritsar", "state": "Punjab"},
    {"city": "Kurukshetra", "state": "Haryana"},
    {"city": "Dwarka", "state": "Gujarat"},
    {"city": "Somnath", "state": "Gujarat"},
    {"city": "Ahmedabad", "state": "Gujarat"},
    {"city": "Surat", "state": "Gujarat"},
    {"city": "Hyderabad", "state": "Telangana"},
    {"city": "Warangal", "state": "Telangana"},
    {"city": "Bhadrachalam", "state": "Telangana"},
    {"city": "Thiruvananthapuram", "state": "Kerala"},
    {"city": "Guruvayur", "state": "Kerala"},
    {"city": "Sabarimala", "state": "Kerala"}
]

async def seed_locations():
    print(f"Seeding {len(CITIES)} locations...")
    
    count = 0
    for loc in CITIES:
        try:
            # Upsert (using city, state as key)
            # Check if exists
            res = supabase.table("locations").select("id").eq("city", loc["city"]).eq("state", loc["state"]).execute()
            if not res.data:
                supabase.table("locations").insert(loc).execute()
                print(f"Added {loc['city']}, {loc['state']}")
                count += 1
            else:
                print(f"Skipped {loc['city']} (exists)")
        except Exception as e:
            print(f"Error adding {loc['city']}: {e}")
            
    print(f"Seeding completed. Added {count} new locations.")

if __name__ == "__main__":
    asyncio.run(seed_locations())
