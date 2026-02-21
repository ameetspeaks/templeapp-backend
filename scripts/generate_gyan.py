"""
generate_gyan.py — Daily Gyan auto-generator using Gemini AI

Usage:
  python scripts/generate_gyan.py --days 30 --start_date 2026-02-01
  python scripts/generate_gyan.py --date 2026-02-21   (single day)
"""

import sys
import os
import asyncio
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.gemini_client import GeminiClient
from app.utils.supabase_client import supabase

load_dotenv()

# Map integer day → seasonal/contextual hint for better Gemini selection
DAY_HINTS = {
    0: "Monday (start of week, motivation)",
    1: "Tuesday (Hanuman Jayanti energy, strength)",
    2: "Wednesday (mid-week, focus)",
    3: "Thursday (Guru Pushya, wisdom and learning)",
    4: "Friday (Lakshmi Puja day, gratitude and abundance)",
    5: "Saturday (Shani day, discipline and karma)",
    6: "Sunday (rest and reflection)",
}

CHAPTER_THEMES = {
    1: "grief, despair, facing challenges",
    2: "immortality of soul, duty, karma",
    3: "karma yoga, selfless action",
    4: "divine knowledge, renunciation",
    5: "renunciation of action, inner peace",
    6: "dhyana yoga, meditation",
    7: "knowledge of the absolute",
    8: "imperishable Brahman, death, rebirth",
    9: "sovereign knowledge, devotion",
    10: "divine glories, manifestations",
    11: "cosmic/universal vision",
    12: "bhakti yoga, devotion",
    13: "field and knower of the field",
    14: "three qualities of nature (gunas)",
    15: "supreme person, yoga of the supreme",
    16: "divine and demoniac natures",
    17: "three divisions of faith",
    18: "liberation, conclusion, moksha",
}


async def generate_single_gyan(date_str: str, gemini: GeminiClient) -> dict | None:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    day_hint = DAY_HINTS[dt.weekday()]

    prompt = f"""
You are a Hindu scriptures expert. Choose ONE highly meaningful shloka from the Bhagavad Gita
that is especially relevant for {date_str} ({day_hint}).

Pick from any chapter based on relevance. Prefer shlokas that give practical, uplifting guidance.

Provide the following JSON:
{{
    "chapter_number": <int 1-18>,
    "verse_number": <int>,
    "sanskrit_text": "<full Sanskrit/Devanagari shloka text>",
    "transliteration": "<Roman transliteration>",
    "hindi_translation": "<concise Hindi translation 1-2 lines>",
    "english_translation": "<concise English translation 1-2 lines>",
    "hindi_meaning": "<deeper Hindi meaning 2-3 sentences>",
    "english_meaning": "<deeper English meaning 2-3 sentences>",
    "daily_message": "<One sentence practical English takeaway for today>",
    "daily_message_hindi": "<One sentence practical Hindi takeaway for today>",
    "practice_for_today": "<One specific action in English the reader can do today>",
    "practice_for_today_hindi": "<Same action in Hindi>",
    "tags": ["<tag1>", "<tag2>", "<tag3>"]
}}

Tags should be from: karma, duty, devotion, peace, knowledge, love, detachment, meditation,
strength, gratitude, surrender, discipline, wisdom, liberation
"""

    try:
        data = await gemini.generate_json(prompt, model="flash")
        data["date"] = date_str
        data["source"] = "Bhagavad Gita"
        return data
    except Exception as e:
        print(f"  ! AI generation failed for {date_str}: {e}")
        return None


async def upsert_gyan(data: dict):
    # Check existing
    res = supabase.table("daily_gyan").select("id").eq("date", data["date"]).execute()
    if res.data:
        row_id = res.data[0]["id"]
        supabase.table("daily_gyan").update(data).eq("id", row_id).execute()
        print(f"  ✓ Updated  [{data['date']}] Gita {data.get('chapter_number')}.{data.get('verse_number')}")
    else:
        supabase.table("daily_gyan").insert(data).execute()
        print(f"  ✓ Inserted [{data['date']}] Gita {data.get('chapter_number')}.{data.get('verse_number')}")


async def generate_gyan(start_date_str: str, days: int = 1):
    gemini = GeminiClient()
    start = datetime.strptime(start_date_str, "%Y-%m-%d").date()

    print(f"\n🕉️  Generating Daily Gyan — Start: {start_date_str}, Days: {days}\n")

    for i in range(days):
        current_date = start + timedelta(days=i)
        date_str = current_date.strftime("%Y-%m-%d")
        print(f"[{i+1}/{days}] Processing {date_str}...")

        data = await generate_single_gyan(date_str, gemini)
        if data:
            await upsert_gyan(data)
        else:
            print(f"  ✗ Skipped {date_str}")

        # Rate-limit courtesy pause every 5 records
        if (i + 1) % 5 == 0:
            await asyncio.sleep(2)

    print("\n✅ Daily Gyan generation complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Aaj Ka Gyan entries using Gemini AI")
    parser.add_argument("--date", type=str, help="Single date YYYY-MM-DD")
    parser.add_argument("--start_date", type=str, help="Start date YYYY-MM-DD")
    parser.add_argument("--days", type=int, default=7, help="Number of days to generate")
    args = parser.parse_args()

    if args.date:
        asyncio.run(generate_gyan(args.date, days=1))
    elif args.start_date:
        asyncio.run(generate_gyan(args.start_date, days=args.days))
    else:
        # Default: generate from today for next 30 days
        today = datetime.now().strftime("%Y-%m-%d")
        asyncio.run(generate_gyan(today, days=30))
