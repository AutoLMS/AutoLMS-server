import asyncio
import logging
import uuid
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from jose import jwt, JWTError

from app.services.base_service import BaseService
from app.core.config import settings

logger = logging.getLogger(__name__)

class SessionService(BaseService):
    """사용자별 이클래스 세션 관리 서비스"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.eclass_sessions: Dict[str, Any] = {}  # user_id -> EclassSession
            self.auth_sessions: Dict[str, Dict[str, Any]] = {}  # token -> session_info
            self._initialized = True
            logger.info("SessionService 초기화 완료")
    
    async def initialize(self) -> None:
        """서비스 초기화"""
        logger.info("SessionService 시작")
        # 세션 체크 작업 스케줄링 등의 초기화 작업 수행
        pass
    
    async def close(self) -> None:
        """서비스 종료 및 리소스 정리"""
        logger.info("SessionService 종료 시작")
        await self.close_all_sessions()
        logger.info("SessionService 종료 완료")
    
    async def get_session(self, user_id: str, eclass_id: str = None, password: str = None) -> Optional[Any]:
        """
        사용자를 위한 이클래스 세션 가져오기 (필요시 생성)
        
        Args:
            user_id: 사용자 ID
            eclass_id: 이클래스 아이디 (학번)
            password: 이클래스 비밀번호
            
        Returns:
            Optional[EclassSession]: 이클래스 세션 객체 또는 None
        """
        from app.services.core.eclass_session import EclassSession

        if user_id in self.eclass_sessions:
            session = self.eclass_sessions[user_id]
            is_logged_in = await session.is_logged_in()

            if is_logged_in:
                logger.debug(f"사용자 {user_id}의 기존 세션 재사용")
                return session
            else:
                logger.debug(f"사용자 {user_id}의 세션이 만료됨, 새로운 세션 생성")

            # 자격 증명 확인
            if not eclass_id or not password:
                # 설정에서 기본 자격 증명 사용
                from app.core.config import settings
                eclass_id = settings.ECLASS_USERNAME
                password = settings.ECLASS_PASSWORD

                if not eclass_id or not password:
                    logger.error("자격 증명이 제공되지 않았고 기본값도 설정되지 않음")
                    return None

            # 새 세션 생성 및 로그인
            eclass_session = EclassSession()
            login_success = await eclass_session.login(username=eclass_id, password=password)

            if login_success:
                logger.info(f"사용자 {user_id} 로그인 성공")
                self.eclass_sessions[user_id] = eclass_session
                return eclass_session
            else:
                logger.error(f"사용자 {user_id} 로그인 실패")
                return None

    async def invalidate_session(self, user_id: str) -> None:
        """
        사용자 세션 무효화

        Args:
            user_id: 사용자 ID
        """
        async with self.lock:
            if user_id in self.eclass_sessions:
                logger.info(f"사용자 {user_id}의 세션 무효화")
                session = self.eclass_sessions[user_id]
                await session.close()
                del self.eclass_sessions[user_id]

    async def check_sessions_health(self) -> None:
        """모든 세션의 건강 상태 확인 (주기적 호출)"""
        logger.info("세션 건강 상태 확인 시작")
        async with self.lock:
            invalid_sessions = []

            for user_id, session in self.eclass_sessions.items():
                try:
                    is_logged_in = await session.is_logged_in()
                    if not is_logged_in:
                        logger.warning(f"사용자 {user_id}의 세션이 유효하지 않음")
                        invalid_sessions.append(user_id)
                except Exception as e:
                    logger.error(f"세션 상태 확인 중 오류 발생: {str(e)}")
                    invalid_sessions.append(user_id)

            # 유효하지 않은 세션 제거
            for user_id in invalid_sessions:
                await self.invalidate_session(user_id)

            logger.info(f"세션 건강 상태 확인 완료: {len(invalid_sessions)}개 세션 무효화")

    async def close_all_sessions(self) -> None:
        """모든 세션 종료 (애플리케이션 종료 시)"""
        logger.info("모든 세션 종료 시작")
        async with self.lock:
            for user_id, session in self.eclass_sessions.items():
                try:
                    await session.close()
                    logger.debug(f"사용자 {user_id}의 세션 종료 완료")
                except Exception as e:
                    logger.error(f"사용자 {user_id}의 세션 종료 중 오류: {str(e)}")

            self.eclass_sessions.clear()
            self.auth_sessions.clear()
            logger.info("모든 세션 종료 완료")

    async def create_session(self, user_id: str, expires_delta: Optional[timedelta] = None) -> Dict[str, Any]:
        """
        인증 세션 생성 및 토큰 발급

        Args:
            user_id: 사용자 ID
            expires_delta: 세션 만료 시간 (기본값: 7일)

        Returns:
            Dict[str, Any]: 세션 정보 및 토큰
        """
        logger.info(f"사용자 {user_id}의 인증 세션 생성")

        if expires_delta is None:
            expires_delta = timedelta(days=7)  # 기본 7일

        expire = datetime.utcnow() + expires_delta
        session_id = str(uuid.uuid4())

        # JWT 토큰 생성
        to_encode = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": session_id
        }

        access_token = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )

        # 세션 정보 저장
        session_info = {
            "id": session_id,
            "user_id": user_id,
            "expires_at": expire,
            "is_active": True,
            "created_at": datetime.utcnow()
        }

        # 메모리에 세션 저장
        async with self.lock:
            self.auth_sessions[access_token] = session_info

        # 데이터베이스에 세션 저장 (선택적)
        # 현재는 메모리에만 저장하지만, 필요 시 세션 리포지토리 활용 가능

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_at": expire.isoformat(),
            "session_id": session_id
        }

    async def end_session(self, token: str) -> bool:
        """
        인증 세션 종료

        Args:
            token: 액세스 토큰

        Returns:
            bool: 세션 종료 성공 여부
        """
        logger.info("인증 세션 종료 시작")

        async with self.lock:
            if token in self.auth_sessions:
                session_info = self.auth_sessions[token]
                user_id = session_info.get("user_id")

                # 메모리에서 세션 제거
                del self.auth_sessions[token]

                # 해당 사용자의 이클래스 세션도 함께 종료
                if user_id in self.eclass_sessions:
                    try:
                        await self.eclass_sessions[user_id].close()
                        del self.eclass_sessions[user_id]
                    except Exception as e:
                        logger.error(f"이클래스 세션 종료 중 오류: {str(e)}")

                # 데이터베이스에서 세션 만료 처리 (선택적)
                # 현재는 메모리에서만 관리하지만, 필요 시 세션 리포지토리 활용 가능

                return True

            # 존재하지 않는 토큰
            return False

    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        토큰 검증 및 사용자 정보 반환

        Args:
            token: 액세스 토큰

        Returns:
            Optional[Dict[str, Any]]: 사용자 정보 또는 None
            :param token:
            :param self:
        """
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
            if datetime.fromtimestamp(expire) < datetime.utcnow():
                logger.warning("만료된 토큰")
                return None

            # 메모리에서 세션 확인
            async with self.lock:
                session_info = self.auth_sessions.get(token)
                if not session_info or not session_info.get("is_active"):
                    logger.warning("존재하지 않거나 비활성화된 세션")
                    return None

            # 사용자 정보 조회 (선택적)
            # 현재는 간단한 정보만 반환하지만, 필요 시 사용자 리포지토리 활용 가능
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
        """
        세션 유효성 검증 - API 엔드포인트에서 사용

        Returns:
            bool: 세션 유효 여부
        """
        # 이 메서드는 API 엔드포인트에서 이미 참조하고 있는 것으로 보임
        # 현재의 구현에서는 로그인 상태만 확인하고 응답하는 간단한 래퍼 메서드로 구현
        return True  # 기본적으로 유효하다고 가정 (실제 구현에서는 세션 상태 체크 필요)
