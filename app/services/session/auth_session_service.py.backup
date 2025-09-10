import logging
import uuid
import asyncio
from typing import Dict, Optional, Any, List, Sequence
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError

from app.core.config import settings
from app.services.base_service import BaseService
from app.db.repositories.session_repository import SessionRepository
from sqlalchemy.ext.asyncio import AsyncSession

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

    def __init__(self, db_session: AsyncSession = None):
        if not self._initialized:
            self.auth_sessions: Dict[str, Dict[str, Any]] = {}  # token -> session_info
            self._lock_ready = False
            self._db = db_session
            self._session_repo = None
            if self._db:
                self._session_repo = SessionRepository(self._db)
            self._initialized = True
            logger.info("AuthSessionService 초기화 완료")

    def set_db_session(self, db_session: AsyncSession):
        """데이터베이스 세션 설정"""
        self._db = db_session
        self._session_repo = SessionRepository(self._db)

    async def _ensure_lock(self):
        """lock이 필요할 때 초기화하는 메서드"""
        if not self._lock_ready:
            self._lock = asyncio.Lock()
            self._lock_ready = True
        return self._lock

    async def initialize(self) -> None:
        """서비스 초기화 및 활성 세션 로드"""
        logger.info("AuthSessionService 시작")
        await self._ensure_lock()  # 초기화 시 락 준비

        # DB에서 활성 세션 로드
        if self._session_repo:
            try:
                active_sessions = await self._session_repo.get_active_sessions()

                # 메모리에 세션 로드
                for session in active_sessions:
                    self.auth_sessions[session.token] = {
                        "id": session.id,
                        "user_id": session.user_id,
                        "eclass_username": session.eclass_username,
                        "expires_at": session.expires_at,
                        "is_active": session.is_active,
                        "created_at": session.created_at
                    }

                logger.info(f"{len(active_sessions)}개의 활성 세션을 메모리에 로드했습니다")
            except Exception as e:
                logger.error(f"DB에서 세션 로드 중 오류: {str(e)}")

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
                # DB에서도 세션 만료 처리
                if self._session_repo:
                    try:
                        session = await self._session_repo.get_by_token(token)
                        if session:
                            await self._session_repo.expire_session(session.id)
                    except Exception as e:
                        logger.error(f"DB에서 세션 만료 처리 중 오류: {str(e)}")

            # 전체 세션 카운트 로깅
            logger.info(f"남은 인증 세션 수: {len(self.auth_sessions)}")

        logger.info("AuthSessionService 종료 완료")

    async def create_session(self, user_id: str, eclass_username: str = None, expires_delta: Optional[timedelta] = None) -> Dict[
        str, Any]:
        """인증 세션 생성 및 토큰 발급"""
        logger.info(f"사용자 {user_id}의 인증 세션 생성")

        if expires_delta is None:
            expires_delta = timedelta(minutes=settings.SESSION_EXPIRE_MINUTES)

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
            algorithm="HS256"
        )

        # 세션 정보 저장
        session_info = {
            "id": session_id,
            "user_id": user_id,
            "eclass_username": eclass_username,
            "token": access_token,
            "expires_at": expire,
            "is_active": True,
            "created_at": datetime.now(timezone.utc)
        }

        # 메모리에 세션 저장
        lock = await self._ensure_lock()
        async with lock:
            self.auth_sessions[access_token] = session_info

        # DB에 세션 저장
        if self._session_repo:
            try:
                await self._session_repo.create(session_info)
                logger.debug(f"세션 {session_id}가 데이터베이스에 저장되었습니다")
            except Exception as e:
                logger.error(f"DB에 세션 저장 중 오류: {str(e)}")

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
            session_info = self.auth_sessions.get(token)

            # 메모리에서 세션 제거
            if token in self.auth_sessions:
                del self.auth_sessions[token]

                # DB에서도 세션 비활성화
                if self._session_repo and session_info:
                    try:
                        await self._session_repo.expire_session(session_info["id"])
                        logger.debug(f"세션 {session_info['id']}가 DB에서 비활성화되었습니다")
                    except Exception as e:
                        logger.error(f"DB에서 세션 비활성화 중 오류: {str(e)}")

                return True

            # DB에서 세션 확인
            if self._session_repo:
                try:
                    session = await self._session_repo.get_by_token(token)
                    if session and session.is_active:
                        await self._session_repo.expire_session(session.id)
                        logger.debug(f"세션 {session.id}가 DB에서만 발견되어 비활성화되었습니다")
                        return True
                except Exception as e:
                    logger.error(f"DB에서 세션 확인 중 오류: {str(e)}")

            # 존재하지 않는 토큰
            return False

    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """토큰 검증 및 사용자 정보 반환"""
        try:
            logger.info(f"토큰 검증 시작: 토큰 길이 {len(token)}자")

            # JWT 토큰 디코딩
            logger.debug(f"JWT 디코딩 시도: {token[:10]}...")
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"]
            )
            logger.info(f"JWT 디코딩 성공: {payload}")

            user_id = payload.get("sub")
            expire = payload.get("exp")
            session_id = payload.get("jti")

            logger.debug(f"Payload 내용: user_id={user_id}, expire={expire}, session_id={session_id}")

            if not user_id:
                logger.warning("토큰에 사용자 ID(sub) 누락")
                return None
            if not expire:
                logger.warning("토큰에 만료 시간(exp) 누락")
                return None
            if not session_id:
                logger.warning("토큰에 세션 ID(jti) 누락")
                return None

            # 만료 시간 확인
            current_time = datetime.now(timezone.utc)
            expiration_time = datetime.fromtimestamp(expire, tz=timezone.utc)
            logger.debug(f"토큰 만료 시간: {expiration_time}, 현재 시간: {current_time}")

            if expiration_time < current_time:
                logger.warning(f"만료된 토큰: 만료={expiration_time}, 현재={current_time}")
                return None

            # 메모리에서 세션 확인
            lock = await self._ensure_lock()
            async with lock:
                logger.debug(f"현재 활성 세션 수: {len(self.auth_sessions)}")
                session_info = self.auth_sessions.get(token)

                # 메모리에 없으면 DB에서 조회
                if not session_info and self._session_repo:
                    try:
                        db_session = await self._session_repo.get_active_session(token)
                        if db_session:
                            logger.debug(f"DB에서 세션 {db_session.id} 찾음, 메모리에 캐싱")
                            # DB에서 가져온 세션 정보를 메모리에 캐싱
                            session_info = {
                                "id": db_session.id,
                                "user_id": db_session.user_id,
                                "eclass_username": db_session.eclass_username,
                                "expires_at": db_session.expires_at,
                                "is_active": db_session.is_active,
                                "created_at": db_session.created_at
                            }
                            self.auth_sessions[token] = session_info
                    except Exception as e:
                        logger.error(f"DB에서 세션 조회 중 오류: {str(e)}")

                logger.debug(f"토큰에 대한 세션 정보: {session_info}")

                if not session_info:
                    logger.warning("세션 정보를 찾을 수 없음 (메모리/DB)")
                    return None
                if not session_info.get("is_active"):
                    logger.warning("세션이 비활성화됨")
                    return None

            logger.info(f"토큰 검증 성공: user_id={user_id}")
            return {
                "id": user_id,
                "eclass_username": session_info.get("eclass_username", "unknown"),
                "session_id": session_id
            }

        except JWTError as e:
            logger.error(f"JWT 디코딩 에러: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"토큰 검증 중 오류: {str(e)}")
            import traceback
            logger.error(f"상세 오류: {traceback.format_exc()}")
            return None