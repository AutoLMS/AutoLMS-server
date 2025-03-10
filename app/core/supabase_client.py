from supabase import create_client, Client
from functools import lru_cache

from app.core.config import settings

@lru_cache()
def get_supabase_client() -> Client:
    """Supabase 클라이언트 초기화 및 캐싱"""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
