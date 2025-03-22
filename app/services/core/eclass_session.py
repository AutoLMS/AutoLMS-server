import asyncio
import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

from app.core.config import settings
from app.db.repositories.session_repository import SessionRepository
from app.db.repositories.user_repository import UserRepository
from app.services.base_service import BaseService
from app.services.eclass_session import EclassSession


logger = logging.getLogger(__name__)


class SessionService(BaseService):
    """통합 세션 관리 서비스 (API 인증 + e-Class 세션)"""

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, db: AsyncSession = None):
        if not self._initialized:
            self._db = db
            self._session_repo = SessionRepository(db) if db else None
            self._user_repo = UserRepository(db) if db else None
            self.eclass_sessions: Dict[str, Any] = {}
            self.lock = asyncio.Lock()
            self._initialized = True
            logger.info("SessionService 초기화 완료")

    # API 세션 관리 메서드들

    async def is_valid(self, token: str) -> bool:
        """API 토큰의 유효성을 검증합니다."""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )

            session_id: str = payload.get("session_id")
            if not session_id:
                return False

            session = await self._session_repo.get_by_id(session_id)
            if not session or not session.is_active:
                return False

            if datetime.utcnow() > session.expires_at:
                return False

            return True
        except JWTError:
            return False

    async def create_session(self, user_id: str) -> Dict[str, Any]:
        """새로운 API 세션을 생성합니다."""
        await self._session_repo.expire_user_sessions(user_id)

        expires_at = datetime.utcnow() + timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
        session = await self._session_repo.create({
            "user_id": user_id,
            "expires_at": expires_at,
            "is_active": True
        })

        token_data = {
            "sub": user_id,
            "session_id": session.id,
            "exp": expires_at
        }
        access_token = jwt.encode(
            token_data,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )

        return {
            "access_token": access_token,
            "expires_at": expires_at,
            "session_id": session.id
        }

    # e-Class 세션 관리 메서드들

    async def get_eclass_session(
            self,
            user_id: str,
            eclass_id: str = None,
            password: str = None
    ) -> Optional[EclassSession]:
        """e-Class 세션을 가져오거나 생성합니다."""
        async with self.lock:
            if user_id in self.eclass_sessions:
                session = self.eclass_sessions[user_id]
                is_logged_in = await session.is_logged_in()

                if is_logged_in:
                    logger.debug(f"사용자 {user_id}의 기존 e-Class 세션 재사용")
                    return session

            if not eclass_id or not password:
                eclass_id = settings.ECLASS_USERNAME
                password = settings.ECLASS_PASSWORD

                if not eclass_id or not password:
                    logger.error("e-Class 자격 증명이 제공되지 않음")
                    return None

            eclass_session = EclassSession()
            login_success = await eclass_session.login(username=eclass_id, password=password)

            if login_success:
                logger.info(f"사용자 {user_id} e-Class 로그인 성공")
                self.eclass_sessions[user_id] = eclass_session
                return eclass_session
            else:
                logger.error(f"사용자 {user_id} e-Class 로그인 실패")
                return None

    async def initialize(self) -> None:
        """서비스 초기화"""
        logger.info("SessionService 시작")
        # TODO: 세션 상태 체크 스케줄러 구현
        pass

    async def close(self) -> None:
        """서비스 종료"""
        logger.info("SessionService 종료 시작")
        await self.close_all_sessions()
        logger.info("SessionService 종료 완료")

    async def check_sessions_health(self) -> None:
        """모든 e-Class 세션의 상태를 확인합니다."""
        logger.info("e-Class 세션 상태 확인 시작")
        async with self.lock:
            invalid_sessions = []

            for user_id, session in self.eclass_sessions.items():
                try:
                    is_logged_in = await session.is_logged_in()
                    if not is_logged_in:
                        logger.warning(f"사용자 {user_id}의 e-Class 세션이 유효하지 않음")
                        invalid_sessions.append(user_id)
                except Exception as e:
                    logger.error(f"세션 상태 확인 중 오류: {str(e)}")
                    invalid_sessions.append(user_id)

            for user_id in invalid_sessions:
                await self.invalidate_session(user_id)

    async def invalidate_session(self, user_id: str) -> None:
        """사용자의 e-Class 세션을 무효화합니다."""
        async with self.lock:
            if user_id in self.eclass_sessions:
                logger.info(f"사용자 {user_id}의 e-Class 세션 무효화")
                session = self.eclass_sessions[user_id]
                await session.close()
                del self.eclass_sessions[user_id]

    async def close_all_sessions(self) -> None:
        """모든 e-Class 세션을 종료합니다."""
        logger.info("모든 e-Class 세션 종료 시작")
        async with self.lock:
            for user_id, session in self.eclass_sessions.items():
                try:
                    await session.close()
                    logger.debug(f"사용자 {user_id}의 e-Class 세션 종료 완료")
                except Exception as e:
                    logger.error(f"사용자 {user_id}의 세션 종료 중 오류: {str(e)}")

            self.eclass_sessions.clear()
            logger.info("모든 e-Class 세션 종료 완료")