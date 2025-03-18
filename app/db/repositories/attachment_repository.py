from typing import List, Dict, Any, Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.repositories.base import BaseRepository
from app.models.attachment import Attachment

class AttachmentRepository(BaseRepository[Attachment]):
    """첨부파일 리포지토리"""
    
    def __init__(self):
        super().__init__(Attachment)
    
    async def get_by_source(self, db: AsyncSession, source_id: Any, source_type: str) -> Sequence[Any]:
        """
        소스별 첨부파일 목록 조회
        반환값: 데이터베이스 모델 객체 목록 (스키마로 변환 필요)
        
        Args:
            db: 데이터베이스 세션
            source_id: 소스 ID (공지사항, 과제, 자료 등의 ID)
            source_type: 소스 타입 ('notices', 'assignments', 'materials' 등)
        """
        query = select(self.model).where(
            self.model.source_type == source_type,
            self.model.source_id == str(source_id)  # source_id를 문자열로 변환
        )
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_by_user_id(self, db: AsyncSession, user_id: str) -> Sequence[Any]:
        """
        사용자별 첨부파일 목록 조회
        반환값: 데이터베이스 모델 객체 목록 (스키마로 변환 필요)
        """
        query = select(self.model).where(self.model.user_id == user_id)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def search(self, db: AsyncSession, user_id: str, query: str) -> Sequence[Any]:
        """
        첨부파일 검색
        반환값: 데이터베이스 모델 객체 목록 (스키마로 변환 필요)
        """
        stmt = select(self.model).where(
            self.model.user_id == user_id,
            self.model.file_name.like(f"%{query}%")
        )
        result = await db.execute(stmt)
        return result.scalars().all()
