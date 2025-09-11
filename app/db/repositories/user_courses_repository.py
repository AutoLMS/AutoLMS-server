from typing import List, Optional, Dict, Any
from supabase import Client, create_client

from app.core.supabase_client import get_supabase_client
from app.core.config import settings

class UserCoursesRepository:
    """사용자-강의 매핑 저장소"""
    
    def __init__(self, use_service_key: bool = False):
        if use_service_key:
            # Service Key 사용 (RLS 우회)
            self.supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
            print("🐛 DEBUG: UserCourses Repository - Service Key 클라이언트 사용")
        else:
            # 일반 클라이언트
            self.supabase: Client = get_supabase_client()
            print("🐛 DEBUG: UserCourses Repository - 일반 클라이언트 사용")
        self.table_name = "user_courses"
    
    async def get_user_courses(self, user_id: str) -> List[Dict[str, Any]]:
        """사용자의 수강 강의 목록 조회 (강의 정보 포함)"""
        try:
            # user_courses와 courses를 조인하여 전체 강의 정보 가져오기
            result = self.supabase.table(self.table_name)\
                .select("""
                    *,
                    courses (
                        id,
                        course_id,
                        course_name,
                        instructor,
                        semester,
                        year,
                        description,
                        last_crawled,
                        created_at,
                        updated_at
                    )
                """)\
                .eq("user_id", user_id)\
                .execute()
            
            return result.data
        except Exception as e:
            print(f"사용자 강의 조회 오류: {e}")
            return []
    
    async def enroll_user_in_course(self, user_id: str, course_id: str) -> Optional[Dict[str, Any]]:
        """사용자를 강의에 등록"""
        try:
            result = self.supabase.table(self.table_name)\
                .upsert({
                    "user_id": user_id,
                    "course_id": course_id,
                    "last_accessed": "now()"
                }, on_conflict="user_id,course_id")\
                .execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"사용자 강의 등록 오류: {e}")
            return None
    
    async def unenroll_user_from_course(self, user_id: str, course_id: str) -> bool:
        """사용자를 강의에서 등록 해제"""
        try:
            result = self.supabase.table(self.table_name)\
                .delete()\
                .eq("user_id", user_id)\
                .eq("course_id", course_id)\
                .execute()
            
            return bool(result.data)
        except Exception as e:
            print(f"사용자 강의 등록 해제 오류: {e}")
            return False
    
    async def update_last_accessed(self, user_id: str, course_id: str) -> bool:
        """사용자의 강의 마지막 접근 시간 업데이트"""
        try:
            result = self.supabase.table(self.table_name)\
                .update({"last_accessed": "now()"})\
                .eq("user_id", user_id)\
                .eq("course_id", course_id)\
                .execute()
            
            return bool(result.data)
        except Exception as e:
            print(f"마지막 접근 시간 업데이트 오류: {e}")
            return False
    
    async def is_user_enrolled(self, user_id: str, course_id: str) -> bool:
        """사용자가 해당 강의에 등록되어 있는지 확인"""
        try:
            result = self.supabase.table(self.table_name)\
                .select("id")\
                .eq("user_id", user_id)\
                .eq("course_id", course_id)\
                .execute()
            
            return bool(result.data)
        except Exception as e:
            print(f"사용자 등록 확인 오류: {e}")
            return False