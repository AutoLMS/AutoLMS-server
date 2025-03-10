from typing import List, Dict, Any, Optional, Sequence
from sqlalchemy.orm import Session

from app.db.repositories.base import BaseRepository
from app.models.course import Course

class CourseRepository(BaseRepository[Course]):
    """강의 리포지토리"""
    
    def __init__(self):
        super().__init__(Course)
    
    async def get_by_user_id(self, db: Session, user_id: str) -> Sequence[Any]:
        """
        사용자 ID로 강의 목록 조회
        반환값: 데이터베이스 모델 객체 목록 (스키마로 변환 필요)
        """
        return db.query(self.model).filter(self.model.user_id == user_id).all()
    
    async def get_by_course_id(self, db: Session, course_id: str, user_id: str) -> Optional[Any]:
        """
        강의 ID로 특정 사용자의 강의 조회
        반환값: 데이터베이스 모델 객체 또는 None (스키마로 변환 필요)
        """
        return db.query(self.model).filter(
            self.model.id == course_id,
            self.model.user_id == user_id
        ).first()
    
    async def exists(self, db: Session, course_id: str, user_id: str) -> bool:
        """
        강의 존재 여부 확인
        반환값: 불리언 값 (True/False)
        """
        result = db.query(self.model).filter(
            self.model.id == course_id,
            self.model.user_id == user_id
        ).first()
        return result is not None
