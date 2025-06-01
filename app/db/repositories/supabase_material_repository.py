from typing import List, Dict, Any
from app.db.repositories.supabase_base_repository import SupabaseBaseRepository

class SupabaseMaterialRepository(SupabaseBaseRepository):
    """Supabase를 사용한 학습자료 저장소"""
    
    def __init__(self):
        super().__init__("materials")
    
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
            print(f"학습자료 조회 오류: {e}")
            return []