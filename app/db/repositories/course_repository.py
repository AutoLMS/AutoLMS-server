from typing import List
from sqlalchemy import select, join
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.repositories.base import BaseRepository
from app.models.course import Course
from app.models.user_courses import user_courses

class CourseRepository(BaseRepository):
    """코스 정보 저장소"""
    
    def __init__(self):
        super().__init__(Course)
    
    async def get_by_user_id(self, db: AsyncSession, user_id: str) -> List[Course]:
        """사용자 ID로 코스 목록 조회"""
        # 사용자와 코스의 다대다 관계를 통해 조회
        query = select(self.model).join(
            user_courses, 
            self.model.id == user_courses.c.course_id
        ).where(
            user_courses.c.user_id == user_id
        )
        
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_course_id(self, db: AsyncSession, course_id: int) -> Course:
        """코스 ID로 단일 코스 조회"""
        query = select(self.model).where(self.model.id == course_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, **kwargs) -> Course:
        """새로운 코스 생성"""
        course = self.model(**kwargs)
        db.add(course)
        await db.commit()
        await db.refresh(course)
        return course

    async def update(self, db: AsyncSession, db_obj: Course, **kwargs) -> Course:
        """코스 정보 업데이트"""
        for key, value in kwargs.items():
            setattr(db_obj, key, value)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj