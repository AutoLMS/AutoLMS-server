import logging
from typing import List, Dict, Any, Optional
from supabase import Client
from app.core.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

class AttachmentRepository:
    """Supabase를 사용한 첨부파일 저장소"""
    
    def __init__(self):
        self.supabase: Client = get_supabase_client()
        self.table_name = "attachments"
    
    async def get_by_id(self, attachment_id: str) -> Optional[Dict[str, Any]]:
        """ID로 첨부파일 조회"""
        try:
            result = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("id", attachment_id)\
                .single()\
                .execute()
            
            return result.data
        except Exception as e:
            logger.error(f"첨부파일 ID 조회 오류: {e}")
            return None
    
    async def get_all(self) -> List[Dict[str, Any]]:
        """모든 첨부파일 조회"""
        try:
            result = self.supabase.table(self.table_name)\
                .select("*")\
                .execute()
            
            return result.data
        except Exception as e:
            logger.error(f"전체 첨부파일 조회 오류: {e}")
            return []
    
    async def get_by_source(self, source_id: str, source_type: str) -> List[Dict[str, Any]]:
        """소스 ID와 타입으로 첨부파일 조회"""
        try:
            result = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("source_id", source_id)\
                .eq("source_type", source_type)\
                .execute()
            
            return result.data
        except Exception as e:
            logger.error(f"첨부파일 소스별 조회 오류: {e}")
            return []
    
    async def create(self, attachment_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """새로운 첨부파일 생성"""
        try:
            result = self.supabase.table(self.table_name)\
                .insert(attachment_data)\
                .execute()
            
            if result.data:
                logger.info(f"첨부파일 생성 완료: {attachment_data.get('file_name', 'Unknown')}")
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"첨부파일 생성 오류: {e}")
            return None
    
    async def upsert(self, attachment_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """첨부파일 생성 또는 업데이트 (source_id + source_type + file_name 중복 체크)"""
        try:
            # 기존 첨부파일 검색
            existing = await self.get_by_source_and_filename(
                attachment_data.get("source_id"),
                attachment_data.get("source_type"), 
                attachment_data.get("file_name")
            )
            
            if existing:
                # 업데이트
                result = self.supabase.table(self.table_name)\
                    .update(attachment_data)\
                    .eq("id", existing["id"])\
                    .execute()
                
                if result.data:
                    logger.info(f"첨부파일 업데이트 완료: {attachment_data.get('file_name', 'Unknown')}")
                    return result.data[0]
            else:
                # 새로 생성
                result = self.supabase.table(self.table_name)\
                    .insert(attachment_data)\
                    .execute()
                
                if result.data:
                    logger.info(f"첨부파일 생성 완료: {attachment_data.get('file_name', 'Unknown')}")
                    return result.data[0]
            
            return None
        except Exception as e:
            logger.error(f"첨부파일 upsert 오류: {e}")
            return None
    
    async def get_by_source_and_filename(self, source_id: str, source_type: str, file_name: str) -> Optional[Dict[str, Any]]:
        """소스 ID, 타입, 파일명으로 첨부파일 조회"""
        try:
            result = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("source_id", source_id)\
                .eq("source_type", source_type)\
                .eq("file_name", file_name)\
                .limit(1)\
                .execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"첨부파일 조회 오류: {e}")
            return None
    
    async def update(self, attachment_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """첨부파일 업데이트"""
        try:
            result = self.supabase.table(self.table_name)\
                .update(kwargs)\
                .eq("id", attachment_id)\
                .execute()
            
            if result.data:
                logger.info(f"첨부파일 업데이트 완료: {attachment_id}")
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"첨부파일 업데이트 오류: {e}")
            return None
    
    async def delete(self, attachment_id: str) -> bool:
        """첨부파일 삭제"""
        try:
            result = self.supabase.table(self.table_name)\
                .delete()\
                .eq("id", attachment_id)\
                .execute()
            
            success = len(result.data) > 0
            if success:
                logger.info(f"첨부파일 삭제 완료: {attachment_id}")
            return success
        except Exception as e:
            logger.error(f"첨부파일 삭제 오류: {e}")
            return False