import logging
from typing import List, Dict, Any, Optional
from supabase import Client, create_client
from app.core.supabase_client import get_supabase_client
from app.core.config import settings

logger = logging.getLogger(__name__)

class AttachmentRepository:
    """Supabase를 사용한 첨부파일 저장소"""
    
    def __init__(self, use_service_key: bool = False):
        if use_service_key:
            # Service Key 사용 (RLS 우회)
            self.supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        else:
            # 일반 클라이언트
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