from typing import List, Dict, Any, Optional, Sequence
from sqlalchemy.orm import Session

from app.db.repositories.base import BaseRepository
from app.models.syllabus import Syllabus

class SyllabusRepository(BaseRepository[Syllabus]):
    """강의 계획서 리포지토리"""
    
    def __init__(self):
        super().__init__(Syllabus)
    
    async def get_by_course_id(self, db: Session, course_id: str) -> Optional[Any]:
        """
        강의 ID로 강의 계획서 조회
        반환값: 데이터베이스 모델 객체 또는 None (스키마로 변환 필요)
        """
        return db.query(self.model).filter(self.model.course_id == course_id).first()
    
    async def exists(self, db: Session, course_id: str) -> bool:
        """
        강의 계획서 존재 여부 확인
        반환값: 불리언 값 (True/False)
        """
        result = db.query(self.model).filter(self.model.course_id == course_id).first()
        return result is not None
