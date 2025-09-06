from typing import List, Optional, Dict, Any
from supabase import Client, create_client

from app.core.supabase_client import get_supabase_client
from app.core.config import settings

class SupabaseCourseRepository:
    """Supabase를 사용한 코스 정보 저장소 (새로운 구조)"""
    
    def __init__(self, use_service_key: bool = False):
        if use_service_key:
            # Service Key 사용 (RLS 우회)
            self.supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
            print("🐛 DEBUG: Course Repository - Service Key 클라이언트 사용")
        else:
            # 일반 클라이언트
            self.supabase: Client = get_supabase_client()
            print("🐛 DEBUG: Course Repository - 일반 클라이언트 사용")
        self.table_name = "courses"
    
    async def get_by_user_id(self, user_id: str) -> List[Dict[str, Any]]:
        """사용자 ID로 코스 목록 조회 (user_courses를 통해)"""
        try:
            # user_courses 테이블을 통해 사용자의 강의 조회
            from app.db.repositories.supabase_user_courses_repository import SupabaseUserCoursesRepository
            user_courses_repo = SupabaseUserCoursesRepository(use_service_key=True)  # Service key 사용
            user_courses = await user_courses_repo.get_user_courses(user_id)
            
            # 강의 정보만 추출
            courses = []
            for uc in user_courses:
                if uc.get('courses'):
                    course_data = uc['courses']
                    # 사용자별 메타데이터 추가
                    course_data['enrollment_date'] = uc.get('enrollment_date')
                    course_data['last_accessed'] = uc.get('last_accessed')
                    courses.append(course_data)
            
            return courses
        except Exception as e:
            print(f"사용자 코스 조회 오류: {e}")
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
    
    async def upsert(self, **kwargs) -> Optional[Dict[str, Any]]:
        """코스 생성 또는 업데이트 (course_id로 중복 체크)"""
        try:
            # user_id 제거 (새로운 구조에서는 courses 테이블에 user_id 없음)
            course_data = {k: v for k, v in kwargs.items() if k != 'user_id'}
            
            result = self.supabase.table(self.table_name)\
                .upsert(course_data, on_conflict="course_id")\
                .execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"코스 upsert 오류: {e}")
            return None
    
    async def upsert_with_user_enrollment(self, user_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """강의 정보를 upsert하고 사용자를 해당 강의에 등록"""
        try:
            # 1. 강의 정보 upsert (user_id 제외)
            course_data = {k: v for k, v in kwargs.items() if k != 'user_id'}
            course_result = await self.upsert(**course_data)
            
            if not course_result:
                return None
                
            # 2. 사용자를 강의에 등록
            from app.db.repositories.supabase_user_courses_repository import SupabaseUserCoursesRepository
            user_courses_repo = SupabaseUserCoursesRepository(use_service_key=True)
            await user_courses_repo.enroll_user_in_course(user_id, course_data['course_id'])
            
            return course_result
        except Exception as e:
            print(f"코스 upsert 및 사용자 등록 오류: {e}")
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