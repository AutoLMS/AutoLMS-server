from typing import List, Optional, Dict, Any
from supabase import Client

from app.core.supabase_client import get_supabase_client

class SupabaseCourseRepository:
    """Supabase를 사용한 코스 정보 저장소"""
    
    def __init__(self):
        self.supabase: Client = get_supabase_client()
        self.table_name = "courses"
    
    async def get_by_user_id(self, user_id: str) -> List[Dict[str, Any]]:
        """사용자 ID로 코스 목록 조회"""
        try:
            result = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("user_id", user_id)\
                .execute()
            
            return result.data
        except Exception as e:
            print(f"코스 조회 오류: {e}")
            return []
    
    async def get_by_course_id(self, course_id: str) -> Optional[Dict[str, Any]]:
        """코스 ID로 단일 코스 조회 (course_id 필드 사용)"""
        try:
            result = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("course_id", course_id)\
                .single()\
                .execute()
            
            return result.data
        except Exception as e:
            print(f"코스 조회 오류: {e}")
            return None
    
    async def create(self, **kwargs) -> Optional[Dict[str, Any]]:
        """새로운 코스 생성"""
        try:
            result = self.supabase.table(self.table_name)\
                .insert(kwargs)\
                .execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"코스 생성 오류: {e}")
            return None
    
    async def update(self, course_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """코스 정보 업데이트"""
        try:
            result = self.supabase.table(self.table_name)\
                .update(kwargs)\
                .eq("id", course_id)\
                .execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"코스 업데이트 오류: {e}")
            return None
    
    async def delete(self, course_id: str) -> bool:
        """코스 삭제"""
        try:
            result = self.supabase.table(self.table_name)\
                .delete()\
                .eq("id", course_id)\
                .execute()
            
            return len(result.data) > 0
        except Exception as e:
            print(f"코스 삭제 오류: {e}")
            return False