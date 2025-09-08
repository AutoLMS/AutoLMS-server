from typing import List, Dict, Any, Optional
from supabase import Client, create_client
from app.core.supabase_client import get_supabase_client
from app.core.config import settings

class SupabaseNoticeRepository:
    """Supabase를 사용한 공지사항 저장소"""
    
    def __init__(self, use_service_key: bool = False):
        if use_service_key:
            # Service Key 사용 (RLS 우회)
            self.supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
            print("🐛 DEBUG: Notice Repository - Service Key 클라이언트 사용")
        else:
            # 일반 클라이언트
            self.supabase: Client = get_supabase_client()
            print("🐛 DEBUG: Notice Repository - 일반 클라이언트 사용")
        self.table_name = "notices"
    
    async def create(self, **kwargs) -> Optional[Dict[str, Any]]:
        """새로운 공지사항 생성"""
        try:
            # article_id를 notice_id로 매핑
            if "article_id" in kwargs and "notice_id" not in kwargs:
                kwargs["notice_id"] = kwargs["article_id"]
            
            result = self.supabase.table(self.table_name)\
                .insert(kwargs)\
                .execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"공지사항 생성 오류: {e}")
            return None
    
    async def get_by_course_id(self, course_id: str) -> List[Dict[str, Any]]:
        """강의 ID로 공지사항 조회"""
        try:
            result = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("course_id", course_id)\
                .order("created_at", desc=True)\
                .execute()
            
            return result.data
        except Exception as e:
            print(f"공지사항 조회 오류: {e}")
            return []
    
    async def get_by_course_and_user(self, course_id: str, user_id: str) -> List[Dict[str, Any]]:
        """강의 ID와 사용자 ID로 공지사항 조회"""
        try:
            result = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("course_id", course_id)\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .execute()
            
            return result.data
        except Exception as e:
            print(f"공지사항 조회 오류: {e}")
            return []