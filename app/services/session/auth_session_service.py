import logging
import uuid
import asyncio
from typing import Dict, Optional, Any
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError

from app.core.config import settings
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class AuthSessionService(BaseService):
    """앱 인증 세션(JWT) 관리 서비스"""

    _instance = None
    _initialized = False
    _lock = None  # 클래스 변수로 lock 선언

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.auth_sessions: Dict[str, Dict[str, Any]] = {}  # token -> session_info
            self._lock_ready = False
            self._initialized = True
            logger.info("AuthSessionService 초기화 완료")

    async def _ensure_lock(self):
        """lock이 필요할 때 초기화하는 메서드"""
        if not self._lock_ready:
            self._lock = asyncio.Lock()
            self._lock_ready = True
        return self._lock

    async def initialize(self) -> None:
        """서비스 초기화"""
        logger.info("AuthSessionService 시작")
        # 세션 체크 작업 스케줄링 등의 초기화 작업 수행
        # 필요 시 추가적인 초기화 작업 구현
        await self._ensure_lock()  # 초기화 시 락 준비
        pass

    async def close(self) -> None:
        """서비스 종료 및 리소스 정리"""
        logger.info("AuthSessionService 종료 시작")

        # 모든 인증 세션 정리
        lock = await self._ensure_lock()
        async with lock:
            expired_tokens = []
            for token, session_info in self.auth_sessions.items():
                try:
                    # 만료된 세션 식별
                    if session_info.get("expires_at", datetime.min.replace(tzinfo=timezone.utc)) < datetime.now(
                            timezone.utc):
                        expired_tokens.append(token)
                except Exception as e:
                    logger.error(f"세션 정리 중 오류: {str(e)}")

            # 만료된 세션 제거
            for token in expired_tokens:
                self.auth_sessions.pop(token, None)

            # 전체 세션 카운트 로깅
            logger.info(f"남은 인증 세션 수: {len(self.auth_sessions)}")

        logger.info("AuthSessionService 종료 완료")

    async def create_session(self, user_id: str, expires_delta: Optional[timedelta] = None) -> Dict[str, Any]:
        """인증 세션 생성 및 토큰 발급"""
        logger.info(f"사용자 {user_id}의 인증 세션 생성")

        if expires_delta is None:
            expires_delta = timedelta(days=7)

        expire = datetime.now(timezone.utc) + expires_delta
        session_id = str(uuid.uuid4())

        # JWT 토큰 생성
        to_encode = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": session_id
        }

        access_token = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
        )

        # 세션 정보 저장
        session_info = {
            "id": session_id,
            "user_id": user_id,
            "expires_at": expire,
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        }

        # 메모리에 세션 저장
        lock = await self._ensure_lock()
        async with lock:
            self.auth_sessions[access_token] = session_info

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_at": expire.isoformat(),
            "session_id": session_id
        }

    async def end_session(self, token: str) -> bool:
        """인증 세션 종료"""
        logger.info("인증 세션 종료 시작")

        lock = await self._ensure_lock()
        async with lock:
            if token in self.auth_sessions:
                # 메모리에서 세션 제거
                del self.auth_sessions[token]
                return True

            # 존재하지 않는 토큰
            return False

    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """토큰 검증 및 사용자 정보 반환"""
        try:
            # JWT 토큰 디코딩
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )

            user_id = payload.get("sub")
            expire = payload.get("exp")
            session_id = payload.get("jti")

            if not user_id or not expire or not session_id:
                logger.warning("유효하지 않은 토큰 페이로드")
                return None

            # 만료 시간 확인
            if datetime.fromtimestamp(expire, tz=timezone.utc) < datetime.now(timezone.utc):
                logger.warning("만료된 토큰")
                return None

            # 메모리에서 세션 확인
            lock = await self._ensure_lock()
            async with lock:
                session_info = self.auth_sessions.get(token)
                if not session_info or not session_info.get("is_active"):
                    logger.warning("존재하지 않거나 비활성화된 세션")
                    return None

            return {
                "id": user_id,
                "token": token,
                "session_id": session_id
            }

        except JWTError as e:
            logger.error(f"JWT 디코딩 에러: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"토큰 검증 중 오류: {str(e)}")
            return None

    async def is_valid(self) -> bool:
        """인증 세션 유효성 검증"""
        try:
            if not self.auth_sessions:
                return False

            for token, session_info in self.auth_sessions.items():
                expires_at = session_info.get("expires_at")
                if expires_at and expires_at < datetime.now(timezone.utc):
                    session_id = session_info.get("id", "알 수 없음")
                    logger.debug(f"세션 {session_id}이 만료됨")
                    return False

            return True
        except Exception as e:
            logger.error(f"인증 세션 유효성 검증 중 오류: {str(e)}")
            return False