import logging
from typing import List, Dict, Any, Optional
from supabase import Client
from app.core.supabase_client import get_supabase_client
from app.core.id_utils import generate_material_id

logger = logging.getLogger(__name__)

class MaterialRepository:
    """Supabase를 사용한 학습자료 저장소"""
    
    def __init__(self):
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
    
    async def create(self, material_data=None, **kwargs) -> Optional[Dict[str, Any]]:
        """새로운 학습자료 생성
        - Composite Key 자동 생성"""
        try:
            # material_data가 딕셔너리로 전달된 경우 kwargs로 언패킹
            if material_data is not None and isinstance(material_data, dict):
                kwargs.update(material_data)
            
            # 필수 필드 확인
            if not kwargs.get('course_id') or not kwargs.get('material_id'):
                raise ValueError("course_id와 material_id는 필수입니다")
                
            # article_id 처리 (이전 버전 호환성)
            if "material_id" not in kwargs and "article_id" in kwargs:
                kwargs["material_id"] = kwargs["article_id"]
            
            # Composite ID 자동 생성
            composite_id = generate_material_id(kwargs['course_id'], kwargs['material_id'])
            kwargs['id'] = composite_id
            
            result = self.supabase.table(self.table_name)\
                .insert(kwargs)\
                .execute()
            
            if result.data:
                logger.info(f"학습자료 생성 완료: {kwargs.get('title', 'Unknown')} (ID: {composite_id})")
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"학습자료 생성 오류: {e}")
            return None
    
    async def upsert(self, **kwargs) -> Optional[Dict[str, Any]]:
        """학습자료 생성 또는 업데이트
        Composite Key 기반"""
        try:
            # 필수 필드 확인
            if not kwargs.get('course_id') or not kwargs.get('material_id'):
                raise ValueError("course_id와 material_id는 필수입니다")
                
            # article_id 처리 (이전 버전 호환성)
            if "material_id" not in kwargs and "article_id" in kwargs:
                kwargs["material_id"] = kwargs["article_id"]
            
            # Composite ID 자동 생성
            composite_id = generate_material_id(kwargs['course_id'], kwargs['material_id'])
            kwargs['id'] = composite_id
            
            result = self.supabase.table(self.table_name)\
                .upsert(kwargs, on_conflict="id")\
                .execute()
            
            if result.data:
                logger.info(f"학습자료 upsert 완료: {kwargs.get('title', 'Unknown')} (ID: {composite_id})")
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