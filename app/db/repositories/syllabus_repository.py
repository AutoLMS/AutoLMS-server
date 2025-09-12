import logging
from typing import List, Dict, Any, Optional
from supabase import Client, create_client
from app.core.supabase_client import get_supabase_client
from app.core.config import settings

logger = logging.getLogger(__name__)

class SyllabusRepository:
    """Supabase를 사용한 강의계획서 저장소"""
    
    def __init__(self, use_service_key: bool = False):
        if use_service_key:
            # Service Key 사용 (RLS 우회)
            self.supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        else:
            # 일반 클라이언트
            self.supabase: Client = get_supabase_client()
        self.table_name = "syllabus"
    
    async def get_by_id(self, syllabus_id: str) -> Optional[Dict[str, Any]]:
        """ID로 강의계획서 조회"""
        try:
            result = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("id", syllabus_id)\
                .single()\
                .execute()
            
            return result.data
        except Exception as e:
            logger.error(f"강의계획서 ID 조회 오류: {e}")
            return None
    
    async def get_by_course_id(self, course_id: str) -> Optional[Dict[str, Any]]:
        """강의 ID로 강의계획서 조회 (JWT 기반 시스템에 맞게 수정)"""
        try:
            result = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("course_id", course_id)\
                .order("created_at", desc=True)\
                .limit(1)\
                .execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"강의계획서 조회 오류: {e}")
            return None
    
    async def get_by_course_and_user(self, course_id: str, user_id: str) -> List[Dict[str, Any]]:
        """강의 ID와 사용자 ID로 강의계획서 조회 (레거시 호환성)"""
        try:
            result = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("course_id", course_id)\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .execute()
            
            return result.data
        except Exception as e:
            logger.error(f"강의계획서 사용자별 조회 오류: {e}")
            return []
    
    async def create(self, **kwargs) -> Optional[Dict[str, Any]]:
        """새로운 강의계획서 생성"""
        try:
            result = self.supabase.table(self.table_name)\
                .insert(kwargs)\
                .execute()
            
            if result.data:
                logger.info(f"강의계획서 생성 완료: {kwargs.get('course_id', 'Unknown')}")
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"강의계획서 생성 오류: {e}")
            return None
    
    async def upsert(self, **kwargs) -> Optional[Dict[str, Any]]:
        """강의계획서 생성 또는 업데이트 (course_id, user_id로 중복 체크)"""
        try:
            result = self.supabase.table(self.table_name)\
                .upsert(kwargs, on_conflict="course_id,user_id")\
                .execute()
            
            if result.data:
                logger.info(f"강의계획서 upsert 완료: {kwargs.get('course_id', 'Unknown')}")
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"강의계획서 upsert 오류: {e}")
            return None
    
    async def update(self, syllabus_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """강의계획서 업데이트"""
        try:
            result = self.supabase.table(self.table_name)\
                .update(kwargs)\
                .eq("id", syllabus_id)\
                .execute()
            
            if result.data:
                logger.info(f"강의계획서 업데이트 완료: {syllabus_id}")
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"강의계획서 업데이트 오류: {e}")
            return None
    
    async def delete(self, syllabus_id: str) -> bool:
        """강의계획서 삭제"""
        try:
            result = self.supabase.table(self.table_name)\
                .delete()\
                .eq("id", syllabus_id)\
                .execute()
            
            success = len(result.data) > 0
            if success:
                logger.info(f"강의계획서 삭제 완료: {syllabus_id}")
            return success
        except Exception as e:
            logger.error(f"강의계획서 삭제 오류: {e}")
            return False