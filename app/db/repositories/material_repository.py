import logging
from typing import List, Dict, Any, Optional
from supabase import Client, create_client
from app.core.supabase_client import get_supabase_client
from app.core.config import settings

logger = logging.getLogger(__name__)

class MaterialRepository:
    """Supabase를 사용한 학습자료 저장소"""
    
    def __init__(self, use_service_key: bool = False):
        if use_service_key:
            # Service Key 사용 (RLS 우회)
            self.supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        else:
            # 일반 클라이언트
            self.supabase: Client = get_supabase_client()
        self.table_name = "materials"
    
    async def get_by_id(self, material_id: str) -> Optional[Dict[str, Any]]:
        """ID로 학습자료 조회"""
        try:
            result = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("id", material_id)\
                .single()\
                .execute()
            
            return result.data
        except Exception as e:
            logger.error(f"학습자료 ID 조회 오류: {e}")
            return None
    
    async def get_by_course_id(self, course_id: str) -> List[Dict[str, Any]]:
        """강의 ID로 강의자료 조회"""
        try:
            result = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("course_id", course_id)\
                .order("created_at", desc=True)\
                .execute()
            
            return result.data
        except Exception as e:
            logger.error(f"강의자료 강의별 조회 오류: {e}")
            return []
    
    async def get_by_course_and_user(self, course_id: str, user_id: str) -> List[Dict[str, Any]]:
        """강의 ID와 사용자 ID로 학습자료 조회"""
        try:
            result = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("course_id", course_id)\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .execute()
            
            return result.data
        except Exception as e:
            logger.error(f"학습자료 사용자별 조회 오류: {e}")
            return []
    
    async def create(self, **kwargs) -> Optional[Dict[str, Any]]:
        """새로운 학습자료 생성"""
        try:
            # material_id 필드 처리
            if "material_id" not in kwargs and "article_id" in kwargs:
                kwargs["material_id"] = kwargs["article_id"]
            
            result = self.supabase.table(self.table_name)\
                .insert(kwargs)\
                .execute()
            
            if result.data:
                logger.info(f"학습자료 생성 완료: {kwargs.get('title', 'Unknown')}")
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"학습자료 생성 오류: {e}")
            return None
    
    async def upsert(self, **kwargs) -> Optional[Dict[str, Any]]:
        """학습자료 생성 또는 업데이트 (material_id로 중복 체크)"""
        try:
            # material_id 필드 처리
            if "material_id" not in kwargs and "article_id" in kwargs:
                kwargs["material_id"] = kwargs["article_id"]
            
            result = self.supabase.table(self.table_name)\
                .upsert(kwargs, on_conflict="material_id,course_id,user_id")\
                .execute()
            
            if result.data:
                logger.info(f"학습자료 upsert 완료: {kwargs.get('title', 'Unknown')}")
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"학습자료 upsert 오류: {e}")
            return None
    
    async def update(self, material_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """학습자료 업데이트"""
        try:
            result = self.supabase.table(self.table_name)\
                .update(kwargs)\
                .eq("id", material_id)\
                .execute()
            
            if result.data:
                logger.info(f"학습자료 업데이트 완료: {material_id}")
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"학습자료 업데이트 오류: {e}")
            return None
    
    async def delete(self, material_id: str) -> bool:
        """학습자료 삭제"""
        try:
            result = self.supabase.table(self.table_name)\
                .delete()\
                .eq("id", material_id)\
                .execute()
            
            success = len(result.data) > 0
            if success:
                logger.info(f"학습자료 삭제 완료: {material_id}")
            return success
        except Exception as e:
            logger.error(f"학습자료 삭제 오류: {e}")
            return False