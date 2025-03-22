from typing import Optional, Dict, Any, List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.db.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    """사용자 리포지토리"""
    
    async def get_by_id(self, db: AsyncSession, user_id: str) -> Optional[User]:
        """사용자 ID로 사용자를 조회합니다."""
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """이메일로 사용자를 조회합니다."""
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        return result.scalars().first()
    
    async def create(self, db: AsyncSession, data: Dict[str, Any]) -> User:
        """새로운 사용자를 생성합니다."""
        user = User(**data)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    async def update(self, db: AsyncSession, user_id: str, data: Dict[str, Any]) -> Optional[User]:
        """사용자 정보를 업데이트합니다."""
        user = await self.get_by_id(db, user_id)
        if not user:
            return None
            
        for field, value in data.items():
            setattr(user, field, value)
            
        await db.commit()
        await db.refresh(user)
        return user
    
    async def get_all(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
        """모든 사용자를 조회합니다."""
        query = select(User).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    async def delete(self, db: AsyncSession, user_id: str) -> bool:
        """사용자를 비활성화합니다 (실제 삭제 대신)."""
        query = update(User).where(User.id == user_id).values(is_active=False)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0
    
    async def get_or_create(self, db: AsyncSession, **kwargs) -> User:
        """
        사용자를 조회하고, 없으면 생성합니다.
        주로 외부 인증 서비스 연동 시 사용합니다.
        """
        # 필수 필드 확인
        email = kwargs.get("email")
        user_id = kwargs.get("id")
        
        if not email or not user_id:
            raise ValueError("사용자 생성에 필요한 필드가 누락되었습니다.")
        
        # 기존 사용자 조회
        user = await self.get_by_id(db, user_id)
        
        # 없으면 생성
        if not user:
            user = await self.create(db, kwargs)
            
        return user
