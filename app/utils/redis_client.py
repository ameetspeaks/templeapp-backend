from upstash_redis import Redis
from app.config import settings

def get_redis_client():
    if not settings.UPSTASH_REDIS_URL or not settings.UPSTASH_REDIS_TOKEN:
        return None
    return Redis(url=settings.UPSTASH_REDIS_URL, token=settings.UPSTASH_REDIS_TOKEN)

redis_client = get_redis_client()
