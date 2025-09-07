from typing import List, Dict, Any
from supabase import Client, create_client
from app.core.supabase_client import get_supabase_client
from app.core.config import settings

class SupabaseAttachmentRepository:
    """Supabase를 사용한 첨부파일 저장소"""
    
    def __init__(self, use_service_key: bool = False):
        if use_service_key:
            # Service Key 사용 (RLS 우회)
            self.supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
            print("🐛 DEBUG: Attachment Repository - Service Key 클라이언트 사용")
        else:
            # 일반 클라이언트
            self.supabase: Client = get_supabase_client()
            print("🐛 DEBUG: Attachment Repository - 일반 클라이언트 사용")
        self.table_name = "attachments"
    
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
            print(f"첨부파일 조회 오류: {e}")
            return []