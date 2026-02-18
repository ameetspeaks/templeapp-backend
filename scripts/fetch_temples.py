import requests
import json
import sys
import os
import asyncio
from slugify import slugify
from dotenv import load_dotenv

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.supabase_client import supabase

load_dotenv()

OVERPASS_URL = "http://overpass-api.de/api/interpreter"

def get_query(city, state):
    # Overpass QL query
    # We look for nodes/ways/relations that are places of worship + hindu
    # and contain the city name in their address or are within the city area.
    # Searching by area is better.
    
    # We first find the area for the city.
    # Then search for temples in that area.
    
    query = f"""
    [out:json][timeout:25];
    area["name"="{city}"]->.searchArea;
    (
      node["amenity"="place_of_worship"]["religion"="hindu"](area.searchArea);
      way["amenity"="place_of_worship"]["religion"="hindu"](area.searchArea);
      relation["amenity"="place_of_worship"]["religion"="hindu"](area.searchArea);
    );
    out center;
    """
    return query

def fetch_osm_data(city, state):
    print(f"Fetching temples for {city}, {state} from OpenStreetMap...")
    query = get_query(city, state)
    try:
        response = requests.get(OVERPASS_URL, params={'data': query})
        response.raise_for_status()
        data = response.json()
        return data.get('elements', [])
    except Exception as e:
        print(f"Error fetching data from OSM: {e}")
        return []

def process_element(element, city, state):
    tags = element.get('tags', {})
    
    name = tags.get('name') or tags.get('name:en') or tags.get('name:hi')
    if not name:
        return None
        
    # Skip generic names if possible, but for now we keep them
    
    # Coordinates
    lat = element.get('lat')
    lon = element.get('lon')
    if not lat or not lon:
        if 'center' in element:
            lat = element['center']['lat']
            lon = element['center']['lon']
    
    if not lat or not lon:
        return None

    # Fields
    deity = tags.get('deity') or "Unknown"
    timings = tags.get('opening_hours') or "Not Available"
    website = tags.get('website') or tags.get('contact:website') or tags.get('url')
    
    # Slug
    osm_id = element.get('id', 0)
    slug = slugify(f"{name} {city} {osm_id}")
    
    # Address Construction
    addr_parts = []
    if tags.get('addr:housenumber'): addr_parts.append(tags['addr:housenumber'])
    if tags.get('addr:street'): addr_parts.append(tags['addr:street'])
    if tags.get('addr:locality'): addr_parts.append(tags['addr:locality'])
    
    full_address = ", ".join(addr_parts)
    if not full_address:
        full_address = f"{name}, {city}, {state}"
    else:
        full_address += f", {city}, {state}"

    # Hero Hint (Simple default)
    hero_hint = f"Ancient temple in {city}"
    
    # Image (Cover URL) - OSM doesn't give good images usually.
    # We leave it null or use a placeholder if required.
    
    return {
        "slug": slug,
        "name": name,
        "deity": deity,
        "city": city,
        "state": state,
        "type": "Temple",
        "timings": timings,
        "hero_hint": hero_hint,
        "latitude": lat,
        "longitude": lon,
        "address": full_address,
        "status": "pending", # To be enriched later
        "contact": tags.get('phone') or tags.get('contact:phone'),
        # JSONB fields defaults
        "darshan_timings": None, # Could parse opening_hours but complex
        "puja_timings": [],
        "major_festivals": [],
        "nearby_attractions": [],
        "interesting_facts": [],
        "website": website # Note: schema might not have website column, check passed schema?
        # Re-checking schema passed by user:
        # id, slug, name, deity, city, state, type, timings, hero_hint, cover_url, lat, lon, address, status, contact, history, significance...
        # It does NOT have 'website' column explicit in the CREATE TABLE snippet.
        # But 'contact' is there. We can put website in description or just ignore for now.
    }

def save_to_supabase(temple_data):
    try:
        # Check if exists by slug
        res = supabase.table("temples").select("id").eq("slug", temple_data['slug']).execute()
        
        # Remove 'website' key if it's not in schema
        if 'website' in temple_data:
            del temple_data['website']
            
        if res.data:
            print(f"  - Updating {temple_data['name']}")
            # Update only empty fields? Or overwrite? 
            # For now overwrite is safer for "fetch fresh data" logic
            supabase.table("temples").update(temple_data).eq("id", res.data[0]['id']).execute()
        else:
            print(f"  - Inserting {temple_data['name']}")
            supabase.table("temples").insert(temple_data).execute()
    except Exception as e:
        print(f"  ! Error saving {temple_data['name']}: {e}")


def fetch_pending_city():
    try:
        # Get one pending city
        # Order by random or id to distribute? Let's just take first.
        res = supabase.table("locations").select("*").eq("status", "pending").order("created_at").limit(1).execute()
        if res.data:
            return res.data[0]
        return None
    except Exception as e:
        print(f"Error fetching pending city: {e}")
        return None

def update_city_status(city_id, status, count=0):
    try:
        supabase.table("locations").update({
            "status": status, 
            "temple_count": count,
            "last_scanned_at": "now()"
        }).eq("id", city_id).execute()
    except Exception as e:
        print(f"Error updating city status: {e}")

def run_batch_mode():
    total_fetched = 0
    max_temples_per_run = 100
    
    print(f"Starting batch mode. Target: {max_temples_per_run} temples.")
    
    while total_fetched < max_temples_per_run:
        location = fetch_pending_city()
        if not location:
            print("No pending cities found.")
            break
            
        city = location['city']
        state = location['state']
        city_id = location['id']
        
        print(f"Processing {city}, {state}...")
        update_city_status(city_id, "processing")
        
        elements = fetch_osm_data(city, state)
        print(f"  Found {len(elements)} items in OSM.")
        
        city_count = 0
        for el in elements:
            temple = process_element(el, city, state)
            if temple:
                save_to_supabase(temple)
                city_count += 1
                total_fetched += 1
        
        # Mark as completed regardless of count (we scanned it)
        # Or if 0, maybe valid 0.
        print(f"  Saved {city_count} temples for {city}.")
        update_city_status(city_id, "completed", count=city_count)
        
        # Check overall limit
        if total_fetched >= max_temples_per_run:
            print(f"Batch limit reached ({total_fetched}). Stopping.")
            break
            
    print(f"Batch run completed. Total temples fetched: {total_fetched}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Fetch Temples from OSM')
    parser.add_argument('--city', type=str, help='City name')
    parser.add_argument('--state', type=str, help='State name')
    parser.add_argument('--batch_mode', action='store_true', help='Run in batch mode fetching from DB')
    
    args = parser.parse_args()
    
    if args.batch_mode:
        run_batch_mode()
    elif args.city and args.state:
        # Legacy single run
        elements = fetch_osm_data(args.city, args.state)
        print(f"Found {len(elements)} items.")
        count = 0
        for el in elements:
            temple = process_element(el, args.city, args.state)
            if temple:
                save_to_supabase(temple)
                count += 1
        print(f"Processed {count} temples for {args.city}.")
    else:
        print("Please provide --city and --state OR --batch_mode")

if __name__ == "__main__":
    main()
