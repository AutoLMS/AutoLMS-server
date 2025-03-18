from typing import List, Dict, Any, Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base import BaseRepository
from app.models.material import Material

class MaterialRepository(BaseRepository[Material]):
    """강의자료 리포지토리"""
    
    def __init__(self):
        super().__init__(Material)
    
    async def get_by_course_id(self, db: AsyncSession, course_id: str) -> Sequence[Material]:
        """
        강의 ID로 강의자료 목록 조회
        반환값: 데이터베이스 모델 객체 목록 (스키마로 변환 필요)
        """
        query = select(self.model).where(self.model.course_id == course_id).order_by(self.model.date.desc())
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_by_article_id(
        self, db: AsyncSession, course_id: str, article_id: str
    ) -> Optional[Material]:
        """
        게시글 ID로 강의자료 조회
        반환값: 데이터베이스 모델 객체 또는 None (스키마로 변환 필요)
        """
        query = select(self.model).where(
            self.model.course_id == course_id,
            self.model.article_id == article_id
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def exists(self, db: AsyncSession, course_id: str, article_id: str) -> bool:
        """
        강의자료 존재 여부 확인
        반환값: 불리언 값 (True/False)
        """
        query = select(self.model).where(
            self.model.course_id == course_id,
            self.model.article_id == article_id
        )
        result = await db.execute(query)
        return result.scalar_one_or_none() is not None