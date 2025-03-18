from typing import List, Dict, Any, Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

from app.db.repositories.base import BaseRepository
from app.models.assignment import Assignment


class AssignmentRepository(BaseRepository[Assignment]):
    """과제 리포지토리"""

    def __init__(self):
        super().__init__(Assignment)

    async def get_by_course_id(self, db: AsyncSession, course_id: str) -> Sequence[Any]:
        """
        강의 ID로 과제 목록 조회
        반환값: 데이터베이스 모델 객체 목록 (스키마로 변환 필요)
        """
        query = select(self.model).where(
            self.model.course_id == course_id
        ).order_by(self.model.due_date.asc())

        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_article_id(self, db: AsyncSession, course_id: str, article_id: str) -> Optional[Any]:
        """
        게시글 ID로 과제 조회
        반환값: 데이터베이스 모델 객체 또는 None (스키마로 변환 필요)
        """
        query = select(self.model).where(
            self.model.course_id == course_id,
            self.model.article_id == article_id
        )

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_upcoming(self, db: AsyncSession, course_id: str) -> Sequence[Any]:
        """
        마감이 임박한 과제 조회
        반환값: 데이터베이스 모델 객체 목록 (스키마로 변환 필요)
        """
        now = datetime.now()
        future = now + timedelta(days=7)  # 1주일 내 마감

        query = select(self.model).where(
            self.model.course_id == course_id,
            self.model.due_date >= now.strftime("%Y-%m-%d"),
            self.model.due_date <= future.strftime("%Y-%m-%d")
        ).order_by(self.model.due_date.asc())

        result = await db.execute(query)
        return result.scalars().all()