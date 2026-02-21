"""
seed_geeta.py — One-time seeder for all 18 Bhagavad Gita chapters and
                selected shlokas from each chapter, using Gemini AI.

Usage:
  python scripts/seed_geeta.py --mode chapters    # Seed chapter metadata only
  python scripts/seed_geeta.py --mode shlokas --chapter 2   # Seed all shlokas for chapter 2
  python scripts/seed_geeta.py --mode all        # Seed everything (long!)
"""

import sys
import os
import asyncio
import argparse
import json
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.gemini_client import GeminiClient
from app.utils.supabase_client import supabase

load_dotenv()

# Ground truth: Chapter counts (authoritative verse counts from the Gita)
CHAPTER_VERSE_COUNTS = {
    1: 47, 2: 72, 3: 43, 4: 42, 5: 29, 6: 47,
    7: 30, 8: 28, 9: 34, 10: 42, 11: 55, 12: 20,
    13: 35, 14: 27, 15: 20, 16: 24, 17: 28, 18: 78
}


async def seed_chapter_metadata(gemini: GeminiClient):
    """Seed all 18 chapter metadata records."""
    print("\n📖 Seeding Chapter metadata (18 chapters)...\n")

    prompt = """
Provide metadata for all 18 chapters of the Bhagavad Gita in JSON array format.
For each chapter include:
{
  "chapter_number": <int>,
  "title": "<English title>",
  "title_hindi": "<Hindi title in Devanagari>",
  "title_sanskrit": "<Sanskrit title in Devanagari>",
  "verse_count": <int>,
  "summary": "<2-3 sentence English summary>",
  "summary_hindi": "<2-3 sentence Hindi summary in Devanagari>",
  "theme": "<One word theme e.g. Karma, Devotion, Knowledge>",
  "key_takeaway": "<One sentence key learning in English>"
}
Return a JSON array of 18 objects.
"""
    try:
        chapters = await gemini.generate_json(prompt, model="pro")
        if isinstance(chapters, dict) and "chapters" in chapters:
            chapters = chapters["chapters"]

        for ch in chapters:
            # Override verse count with authoritative data
            ch_num = ch.get("chapter_number")
            if ch_num in CHAPTER_VERSE_COUNTS:
                ch["verse_count"] = CHAPTER_VERSE_COUNTS[ch_num]

            res = supabase.table("geeta_chapters").select("chapter_number").eq("chapter_number", ch_num).execute()
            if res.data:
                supabase.table("geeta_chapters").update(ch).eq("chapter_number", ch_num).execute()
                print(f"  ✓ Updated Chapter {ch_num}: {ch.get('title')}")
            else:
                supabase.table("geeta_chapters").insert(ch).execute()
                print(f"  ✓ Inserted Chapter {ch_num}: {ch.get('title')}")

    except Exception as e:
        print(f"  ✗ Failed to seed chapters: {e}")


async def seed_chapter_shlokas(chapter_number: int, gemini: GeminiClient, batch_size: int = 10):
    """Seed all shlokas for a single chapter in batches."""
    verse_count = CHAPTER_VERSE_COUNTS.get(chapter_number, 20)
    print(f"\n📜 Seeding Chapter {chapter_number} ({verse_count} shlokas)...\n")

    for batch_start in range(1, verse_count + 1, batch_size):
        batch_end = min(batch_start + batch_size - 1, verse_count)
        verses_range = list(range(batch_start, batch_end + 1))

        prompt = f"""
Provide accurate data for Bhagavad Gita Chapter {chapter_number}, verses {batch_start} to {batch_end}.
Return a JSON array. For each verse:
{{
  "chapter_number": {chapter_number},
  "verse_number": <int>,
  "sanskrit_text": "<Full authentic Sanskrit/Devanagari text>",
  "transliteration": "<IAST or readable Roman transliteration>",
  "hindi_translation": "<Concise Hindi translation in Devanagari>",
  "english_translation": "<Concise English translation>",
  "hindi_meaning": "<Deeper Hindi meaning 2-3 sentences>",
  "english_meaning": "<Deeper English meaning 2-3 sentences>",
  "word_by_word": [
    {{"sanskrit": "<word>", "transliteration": "<transliteration>", "hindi": "<hindi>", "english": "<english>"}}
  ],
  "tags": ["<tag1>", "<tag2>"]
}}
Ensure Sanskrit text is authentic. Provide verses {batch_start} through {batch_end} for chapter {chapter_number}.
"""
        try:
            shlokas = await gemini.generate_json(prompt, model="flash")
            if isinstance(shlokas, dict):
                # Handle wrapped response
                for key in ["shlokas", "verses", "data"]:
                    if key in shlokas:
                        shlokas = shlokas[key]
                        break

            if not isinstance(shlokas, list):
                print(f"  ✗ Unexpected format for Ch{chapter_number} v{batch_start}-{batch_end}")
                continue

            for s in shlokas:
                ch = s.get("chapter_number", chapter_number)
                v = s.get("verse_number")
                if not v:
                    continue
                shloka_id = f"{ch}.{v}"
                s["id"] = shloka_id

                res = supabase.table("geeta_shlokas").select("id").eq("id", shloka_id).execute()
                if res.data:
                    supabase.table("geeta_shlokas").update(s).eq("id", shloka_id).execute()
                    print(f"  ✓ Updated  Shloka {shloka_id}")
                else:
                    supabase.table("geeta_shlokas").insert(s).execute()
                    print(f"  ✓ Inserted Shloka {shloka_id}")

            await asyncio.sleep(1)  # Rate limit

        except Exception as e:
            print(f"  ✗ Error seeding Ch{chapter_number} v{batch_start}-{batch_end}: {e}")


async def seed_all(gemini: GeminiClient):
    await seed_chapter_metadata(gemini)
    for ch_num in range(1, 19):
        await seed_chapter_shlokas(ch_num, gemini)
        await asyncio.sleep(2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Bhagavad Gita data into Supabase")
    parser.add_argument("--mode", choices=["chapters", "shlokas", "all"], default="chapters")
    parser.add_argument("--chapter", type=int, help="Chapter number (for --mode shlokas)")
    parser.add_argument("--batch_size", type=int, default=10, help="Shlokas per AI call")
    args = parser.parse_args()

    gemini = GeminiClient()

    if args.mode == "chapters":
        asyncio.run(seed_chapter_metadata(gemini))
    elif args.mode == "shlokas":
        if not args.chapter:
            print("Please specify --chapter <number> for shlokas mode")
            sys.exit(1)
        asyncio.run(seed_chapter_shlokas(args.chapter, gemini, args.batch_size))
    elif args.mode == "all":
        asyncio.run(seed_all(gemini))

    print("\n✅ Done!")
