from typing import List, Dict, Any, Optional, Sequence
from sqlalchemy.orm import Session

from app.db.repositories.base import BaseRepository
from app.models.attachment import Attachment

class AttachmentRepository(BaseRepository[Attachment]):
    """첨부파일 리포지토리"""
    
    def __init__(self):
        super().__init__(Attachment)
    
    async def get_by_source(self, db: Session, source_type: str, source_id: str) -> Sequence[Any]:
        """
        소스별 첨부파일 목록 조회
        반환값: 데이터베이스 모델 객체 목록 (스키마로 변환 필요)
        """
        return db.query(self.model).filter( 
            self.model.source_type == source_type,
            self.model.source_id == source_id
        ).all()
    
    async def get_by_user_id(self, db: Session, user_id: str) -> Sequence[Any]:
        """
        사용자별 첨부파일 목록 조회
        반환값: 데이터베이스 모델 객체 목록 (스키마로 변환 필요)
        """
        return db.query(self.model).filter(self.model.user_id == user_id).all()
    
    async def search(self, db: Session, user_id: str, query: str) -> Sequence[Any]:
        """
        첨부파일 검색
        반환값: 데이터베이스 모델 객체 목록 (스키마로 변환 필요)
        """
        return db.query(self.model).filter(
            self.model.user_id == user_id,
            self.model.file_name.like(f"%{query}%")
        ).all()
