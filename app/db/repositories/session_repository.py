from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.session import Session


class SessionRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_id(self, session_id: str) -> Optional[Session]:
        """세션 ID로 세션을 조회합니다."""
        result = await self._db.execute(
            select(Session).where(Session.id == session_id)
        )
        return result.scalar_one_or_none()

    async def create(self, data: Dict[str, Any]) -> Session:
        """새로운 세션을 생성합니다."""
        session = Session(**data)
        self._db.add(session)
        await self._db.commit()
        await self._db.refresh(session)
        return session

    async def expire_session(self, session_id: str) -> bool:
        """특정 세션을 만료 처리합니다."""
        result = await self._db.execute(
            update(Session)
            .where(Session.id == session_id)
            .values(
                is_active=False,
                expires_at=datetime.utcnow()
            )
        )
        await self._db.commit()
        return result.rowcount > 0

    async def expire_user_sessions(self, user_id: str) -> bool:
        """사용자의 모든 활성 세션을 만료 처리합니다."""
        result = await self._db.execute(
            update(Session)
            .where(
                Session.user_id == user_id,
                Session.is_active == True
            )
            .values(
                is_active=False,
                expires_at=datetime.utcnow()
            )
        )
        await self._db.commit()
        return result.rowcount > 0