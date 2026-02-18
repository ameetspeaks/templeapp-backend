import asyncio
from datetime import datetime, timedelta
from app.services.panchang_calculator import PanchangCalculator
from app.services.gemini_client import GeminiClient
from app.utils.supabase_client import supabase
from app.utils.logger import setup_logger

logger = setup_logger("jobs")
panchang_calc = PanchangCalculator()
gemini = GeminiClient()

async def job_generate_panchang():
    logger.info("Starting Panchang Generation Job")
    city = "Delhi"
    try:
        for i in range(7):
            date = datetime.now() + timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            
            calc = panchang_calc.calculate(date_str, city)
            prompt = f"""
            Generate a daily panchang description based on this data: {calc}.
            Output JSON: hindi_description, english_description, spiritual_message, festivals.
            """
            try:
                ai = await gemini.generate_json(prompt, model="flash")
                full = {**calc, **ai}
                
                res = supabase.table("panchang_daily").select("id").eq("date", date_str).eq("city", city).execute()
                if res.data:
                    supabase.table("panchang_daily").update(full).eq("id", res.data[0]['id']).execute()
                else:
                    supabase.table("panchang_daily").insert(full).execute()
            except Exception as e:
                logger.error(f"Failed for date {date_str}: {e}")
                
        logger.info("Panchang Generation Job Completed")
    except Exception as e:
        logger.error(f"Panchang Job Failed: {e}")

async def job_generate_blogs():
    logger.info("Starting Blog Generation Job")
    try:
        # Generate 2 blogs
        for _ in range(2):
            # Fetch keyword
            res = supabase.table("blog_keywords").select("*").eq("is_used", False).order("priority", desc=True).limit(1).execute()
            if not res.data:
                logger.info("No keywords available for blog generation")
                break
                
            keyword_data = res.data[0]
            keyword = keyword_data['keyword']
            category = keyword_data.get('category', 'General')
            
            prompt = f"""
            Write SEO blog for: "{keyword}", Category: {category}.
            JSON: title, meta_description, slug, content_html, faqs, tags, category, estimated_word_count.
            """
            
            blog_data = await gemini.generate_json(prompt, model="pro")
            
            db_data = {
                "title": blog_data['title'],
                "slug": blog_data['slug'],
                "meta_description": blog_data['meta_description'],
                "content_html": blog_data['content_html'],
                "faqs": blog_data['faqs'],
                "tags": blog_data['tags'],
                "category": blog_data['category'],
                "status": "draft",
                "ai_generated": True,
                "keyword_id": keyword_data['id'],
                "created_at": datetime.now().isoformat()
            }
            
            supabase.table("blogs").insert(db_data).execute()
            supabase.table("blog_keywords").update({"is_used": True, "used_at": datetime.now().isoformat()}).eq("id", keyword_data['id']).execute()
            
            await asyncio.sleep(5) # Delay
            
        logger.info("Blog Generation Job Completed")
    except Exception as e:
        logger.error(f"Blog Job Failed: {e}")

# Other jobs would follow similar pattern
async def job_enrich_temples():
    logger.info("Starting Temple Enrichment Job")
    # Implementation placeholder
    pass

async def job_generate_muhurat_report():
    logger.info("Starting Muhurat Report Job")
    pass

async def job_generate_aarti_lyrics():
    logger.info("Starting Aarti Lyrics Job")
    pass

async def job_fetch_aarti_audio():
    logger.info("Starting Aarti Audio Job")
    pass
