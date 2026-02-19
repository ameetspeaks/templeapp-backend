
import sys
import os
import asyncio
from dotenv import load_dotenv

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.gemini_client import GeminiClient
from app.utils.supabase_client import supabase
from datetime import datetime

load_dotenv()

async def generate_blog_post():
    print("Starting Blog Generation...")
    
    # 1. Fetch unused keyword
    res = supabase.table("blog_keywords").select("*").eq("is_used", False).order("priority", desc=True).limit(1).execute()
    
    if not res.data:
        print("No unused keywords found.")
        return

    keyword_data = res.data[0]
    keyword = keyword_data['keyword']
    category = keyword_data.get('category', 'General')
    
    print(f"Generating blog for: {keyword} ({category})")
    
    gemini = GeminiClient()
    
    # 2. Generate Content
    prompt = f"""
    Write a high-quality SEO blog post about: "{keyword}".
    Category: {category}
    Target Audience: Devotional Hindu app users.
    
    Requirements:
    - 1200-1500 words, warm devotional tone, English.
    - Structure: H1, Meta Description, Slug, 5-6 H2s, CTA "Use TempleApp", FAQ (5 items), Conclusion.
    - Return strict JSON.
    
    JSON Structure:
    {{
        "title": "H1 title",
        "meta_description": "Max 155 chars",
        "slug": "url-safe-slug",
        "content_html": "Full HTML content excluding title",
        "faqs": [{{"question": "...", "answer": "..."}}],
        "tags": ["tag1", "tag2"],
        "category": "{category}",
        "estimated_word_count": 1200
    }}
    """
    
    try:
        blog_data = await gemini.generate_json(prompt, model="pro")
        
        # 3. Save to Drafts
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
        
        insert_res = supabase.table("blogs").insert(db_data).execute()
        
        # 4. Mark keyword as used
        supabase.table("blog_keywords").update({"is_used": True, "used_at": datetime.now().isoformat()}).eq("id", keyword_data['id']).execute()
        
        print(f"Successfully generated blog: {blog_data['title']}")
        
    except Exception as e:
        print(f"Error generating blog: {e}")

if __name__ == "__main__":
    asyncio.run(generate_blog_post())
