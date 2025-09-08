from typing import List, Dict, Any
from supabase import Client, create_client
from app.core.supabase_client import get_supabase_client
from app.core.config import settings

class SupabaseSyllabusRepository:
    """Supabase를 사용한 강의계획서 저장소"""
    
    def __init__(self, use_service_key: bool = False):
        if use_service_key:
            # Service Key 사용 (RLS 우회)
            self.supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
            print("🐛 DEBUG: Syllabus Repository - Service Key 클라이언트 사용")
        else:
            # 일반 클라이언트
            self.supabase: Client = get_supabase_client()
            print("🐛 DEBUG: Syllabus Repository - 일반 클라이언트 사용")
        self.table_name = "syllabus"
    
    async def create(self, **kwargs) -> Dict[str, Any]:
        """새로운 강의계획서 생성"""
        try:
            result = self.supabase.table(self.table_name)\
                .insert(kwargs)\
                .execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"강의계획서 생성 오류: {e}")
            return None
    
    async def update(self, id_value: str, **kwargs) -> Dict[str, Any]:
        """강의계획서 업데이트"""
        try:
            result = self.supabase.table(self.table_name)\
                .update(kwargs)\
                .eq("id", id_value)\
                .execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"강의계획서 업데이트 오류: {e}")
            return None
    
    async def get_by_course_and_user(self, course_id: str, user_id: str) -> List[Dict[str, Any]]:
        """강의 ID와 사용자 ID로 강의계획서 조회"""
        try:
            result = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("course_id", course_id)\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .execute()
            
            return result.data
        except Exception as e:
            print(f"강의계획서 조회 오류: {e}")
            return []