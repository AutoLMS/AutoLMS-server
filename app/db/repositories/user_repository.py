from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base import BaseRepository
from app.models.user import User


class UserRepository(BaseRepository):
    """사용자 정보 저장소"""
    
    def __init__(self):
        super().__init__(User)
    
    async def get_by_id(self, db: AsyncSession, user_id: str) -> Optional[User]:
        """사용자 ID로 사용자 조회"""
        query = select(self.model).where(self.model.id == user_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_eclass_username(self, db: AsyncSession, eclass_username: str) -> Optional[User]:
        """e-Class 사용자명으로 사용자 조회"""
        query = select(self.model).where(self.model.eclass_username == eclass_username)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, **kwargs) -> User:
        """새로운 사용자 생성"""
        user = self.model(**kwargs)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def update(self, db: AsyncSession, db_obj: User, **kwargs) -> User:
        """사용자 정보 업데이트"""
        for key, value in kwargs.items():
            setattr(db_obj, key, value)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, user_id: str) -> bool:
        """사용자 삭제"""
        user = await self.get_by_id(db, user_id)
        if user:
            await db.delete(user)
            await db.commit()
            return True
        return False

    async def exists(self, db: AsyncSession, user_id: str) -> bool:
        """사용자 존재 여부 확인"""
        user = await self.get_by_id(db, user_id)
        return user is not None