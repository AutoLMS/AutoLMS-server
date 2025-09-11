from typing import List, Optional, Dict, Any
from supabase import Client

from app.core.supabase_client import get_supabase_client

class BaseRepository:
    """Supabase를 사용한 기본 저장소 클래스"""
    
    def __init__(self, table_name: str):
        self.supabase: Client = get_supabase_client()
        self.table_name = table_name
    
    async def get_all(self, **filters) -> List[Dict[str, Any]]:
        """모든 레코드 조회 (필터 적용 가능)"""
        try:
            query = self.supabase.table(self.table_name).select("*")
            
            for key, value in filters.items():
                query = query.eq(key, value)
            
            result = query.execute()
            return result.data
        except Exception as e:
            print(f"{self.table_name} 조회 오류: {e}")
            return []
    
    async def get_by_id(self, id_value: str) -> Optional[Dict[str, Any]]:
        """ID로 단일 레코드 조회"""
        try:
            result = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("id", id_value)\
                .single()\
                .execute()
            
            return result.data
        except Exception as e:
            print(f"{self.table_name} ID 조회 오류: {e}")
            return None
    
    async def create(self, **kwargs) -> Optional[Dict[str, Any]]:
        """새로운 레코드 생성"""
        try:
            # 테이블별로 필수 ID 필드 추가
            if self.table_name == "notices" and "notice_id" not in kwargs:
                if "article_id" in kwargs:
                    kwargs["notice_id"] = kwargs["article_id"]
                else:
                    print(f"notices 테이블: article_id가 필요합니다")
                    return None
                    
            elif self.table_name == "materials" and "material_id" not in kwargs:
                if "article_id" in kwargs:
                    kwargs["material_id"] = kwargs["article_id"]
                else:
                    print(f"materials 테이블: article_id가 필요합니다")
                    return None
                    
            elif self.table_name == "assignments" and "assignment_id" not in kwargs:
                if "article_id" in kwargs:
                    kwargs["assignment_id"] = kwargs["article_id"]
                else:
                    print(f"assignments 테이블: article_id가 필요합니다")
                    return None
            
            result = self.supabase.table(self.table_name)\
                .insert(kwargs)\
                .execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"{self.table_name} 생성 오류: {e}")
            return None
    
    async def update(self, id_value: str, **kwargs) -> Optional[Dict[str, Any]]:
        """레코드 업데이트"""
        try:
            result = self.supabase.table(self.table_name)\
                .update(kwargs)\
                .eq("id", id_value)\
                .execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"{self.table_name} 업데이트 오류: {e}")
            return None
    
    async def delete(self, id_value: str) -> bool:
        """레코드 삭제"""
        try:
            result = self.supabase.table(self.table_name)\
                .delete()\
                .eq("id", id_value)\
                .execute()
            
            return len(result.data) > 0
        except Exception as e:
            print(f"{self.table_name} 삭제 오류: {e}")
            return False
    
    async def get_by_user_id(self, user_id: str) -> List[Dict[str, Any]]:
        """사용자 ID로 레코드 목록 조회"""
        try:
            result = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("user_id", user_id)\
                .execute()
            
            return result.data
        except Exception as e:
            print(f"{self.table_name} 사용자별 조회 오류: {e}")
            return []
    
    async def get_by_course_id(self, course_id: str) -> List[Dict[str, Any]]:
        """강의 ID로 레코드 목록 조회"""
        try:
            # course_id를 그대로 문자열로 사용 (스키마 수정 후)
            result = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("course_id", course_id)\
                .execute()
            
            return result.data
        except Exception as e:
            print(f"{self.table_name} 강의별 조회 오류: {e}")
            return []