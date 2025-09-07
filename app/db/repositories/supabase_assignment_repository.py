from typing import List, Dict, Any
from supabase import Client, create_client
from app.core.supabase_client import get_supabase_client
from app.core.config import settings

class SupabaseAssignmentRepository:
    """Supabase를 사용한 과제 저장소"""
    
    def __init__(self, use_service_key: bool = False):
        if use_service_key:
            # Service Key 사용 (RLS 우회)
            self.supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
            print("🐛 DEBUG: Assignment Repository - Service Key 클라이언트 사용")
        else:
            # 일반 클라이언트
            self.supabase: Client = get_supabase_client()
            print("🐛 DEBUG: Assignment Repository - 일반 클라이언트 사용")
        self.table_name = "assignments"
    
    async def get_by_course_id(self, course_id: str) -> List[Dict[str, Any]]:
        """강의 ID로 과제 조회"""
        try:
            result = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("course_id", course_id)\
                .order("created_at", desc=True)\
                .execute()
            
            return result.data
        except Exception as e:
            print(f"과제 조회 오류: {e}")
            return []
    
    async def get_by_course_and_user(self, course_id: str, user_id: str) -> List[Dict[str, Any]]:
        """강의 ID와 사용자 ID로 과제 조회"""
        try:
            result = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("course_id", course_id)\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .execute()
            
            return result.data
        except Exception as e:
            print(f"과제 조회 오류: {e}")
            return []