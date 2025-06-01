from typing import List, Dict, Any
from app.db.repositories.supabase_base_repository import SupabaseBaseRepository

class SupabaseAttachmentRepository(SupabaseBaseRepository):
    """Supabase를 사용한 첨부파일 저장소"""
    
    def __init__(self):
        super().__init__("attachments")
    
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