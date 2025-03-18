from typing import List, Dict, Any, Optional, TypeVar, Generic, Type, Union, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """기본 SQLAlchemy 리포지토리"""
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    async def get_by_id(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """
        ID로 항목 조회
        반환값: 데이터베이스 모델 객체 또는 None
        """
        query = select(self.model).where(self.model.id == id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_all(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> Sequence[ModelType]:
        """
        모든 항목 조회
        반환값: 데이터베이스 모델 객체 목록
        """
        query = select(self.model).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def create(self, db: AsyncSession, obj_data: Dict[str, Any]) -> ModelType:
        """
        새 항목 생성
        반환값: 생성된 데이터베이스 모델 객체
        """
        db_obj = self.model(**obj_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def update(
        self, db: AsyncSession, id: Any, obj_data: Dict[str, Any]
    ) -> Optional[ModelType]:
        """
        항목 업데이트
        반환값: 업데이트된 데이터베이스 모델 객체 또는 None
        """
        db_obj = await self.get_by_id(db, id)
        if not db_obj:
            return None
            
        for key, value in obj_data.items():
            setattr(db_obj, key, value)
            
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def delete(self, db: AsyncSession, id: Any) -> bool:
        """
        항목 삭제
        반환값: 삭제 성공 여부 (불리언)
        """
        db_obj = await self.get_by_id(db, id)
        if not db_obj:
            return False
            
        await db.delete(db_obj)
        await db.commit()
        return True