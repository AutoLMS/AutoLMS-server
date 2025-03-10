from typing import List, Dict, Any, Optional, TypeVar, Generic, Type, Union, Sequence
from sqlalchemy.orm import Session
from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """기본 SQLAlchemy 리포지토리"""
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    async def get_by_id(self, db: Session, id: Any) -> Optional[Any]:
        """
        ID로 항목 조회
        반환값: 데이터베이스 모델 객체 또는 None
        """
        return db.query(self.model).filter(self.model.id == id).first()
    
    async def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> Sequence[Any]:
        """
        모든 항목 조회
        반환값: 데이터베이스 모델 객체 목록
        """
        return db.query(self.model).offset(skip).limit(limit).all()
    
    async def create(self, db: Session, obj_data: Dict[str, Any]) -> Union[int, str]:
        """
        새 항목 생성
        반환값: 생성된 항목의 ID (정수 또는 문자열)
        """
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj.id
    
    async def update(self, db: Session, id: Any, obj_data: Dict[str, Any]) -> Optional[Any]:
        """
        항목 업데이트
        반환값: 업데이트된 데이터베이스 모델 객체 또는 None
        """
        db_obj = await self.get_by_id(db, id)
        if not db_obj:
            return None
            
        for key, value in obj_data.items():
            setattr(db_obj, key, value)
            
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    async def delete(self, db: Session, id: Any) -> bool:
        """
        항목 삭제
        반환값: 삭제 성공 여부 (불리언)
        """
        db_obj = await self.get_by_id(db, id)
        if not db_obj:
            return False
            
        db.delete(db_obj)
        db.commit()
        return True
