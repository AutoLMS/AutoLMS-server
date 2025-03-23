import logging
import asyncio
from typing import Dict, Optional

from app.services.base_service import BaseService
from app.services.session.eclass_session import EclassSession

logger = logging.getLogger(__name__)


class EclassSessionManager(BaseService):
    """이클래스 세션 관리 서비스"""

    _instance = None
    _initialized = False
    _lock = None  # 클래스 변수로 lock 선언

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.eclass_sessions: Dict[str, EclassSession] = {}  # user_id -> EclassSession
            self._lock_ready = False
            self._initialized = True
            logger.info("EclassSessionManager 초기화 완료")

    async def _ensure_lock(self):
        """lock이 필요할 때 초기화하는 메서드"""
        if not self._lock_ready:
            self._lock = asyncio.Lock()
            self._lock_ready = True
        return self._lock

    async def initialize(self) -> None:
        """서비스 초기화"""
        logger.info("EclassSessionManager 시작")
        # 세션 체크 작업 스케줄링 등의 초기화 작업 수행
        # Todo: 주기적인 세션 건강 상태 확인 스케줄링
        await self._ensure_lock()  # 초기화 시 락 준비
        pass

    async def close(self) -> None:
        """서비스 종료 및 리소스 정리"""
        logger.info("EclassSessionManager 종료 시작")
        await self.close_all_sessions()
        logger.info("EclassSessionManager 종료 완료")

    async def get_session(self, user_id: str, eclass_id: str, password: str) -> Optional[EclassSession]:
        """
        사용자를 위한 이클래스 세션 가져오기 (필요시 생성)

        Args:
            user_id: 사용자 ID
            eclass_id: 이클래스 아이디 (학번) - 필수
            password: 이클래스 비밀번호 - 필수

        Returns:
            Optional[EclassSession]: 이클래스 세션 객체 또는 None
        """
        lock = await self._ensure_lock()
        async with lock:
            if user_id in self.eclass_sessions:
                session = self.eclass_sessions[user_id]
                is_logged_in = await session.is_logged_in()

                if is_logged_in:
                    logger.debug(f"사용자 {user_id}의 기존 세션 재사용")
                    return session
                else:
                    logger.debug(f"사용자 {user_id}의 세션이 만료됨, 새로운 세션 생성")

            # 자격 증명 확인 - 반드시 직접 제공되어야 함
            if not eclass_id or not password:
                logger.error("이클래스 자격 증명이 제공되지 않았습니다")
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
        """사용자 세션 무효화"""
        lock = await self._ensure_lock()
        async with lock:
            if user_id in self.eclass_sessions:
                logger.info(f"사용자 {user_id}의 세션 무효화")
                session = self.eclass_sessions[user_id]
                await session.close()
                del self.eclass_sessions[user_id]

    async def check_sessions_health(self) -> None:
        """모든 세션의 건강 상태 확인 (주기적 호출)"""
        logger.info("세션 건강 상태 확인 시작")
        lock = await self._ensure_lock()
        async with lock:
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
        lock = await self._ensure_lock()
        async with lock:
            for user_id, session in self.eclass_sessions.items():
                try:
                    await session.close()
                    logger.debug(f"사용자 {user_id}의 세션 종료 완료")
                except Exception as e:
                    logger.error(f"사용자 {user_id}의 세션 종료 중 오류: {str(e)}")

            self.eclass_sessions.clear()
            logger.info("모든 세션 종료 완료")

    async def is_valid(self) -> bool:
        """이클래스 세션 유효성 검증"""
        try:
            if not self.eclass_sessions:
                return False

            for user_id, session in self.eclass_sessions.items():
                if not await session.is_logged_in():
                    logger.debug(f"사용자 {user_id}의 이클래스 세션이 유효하지 않음")
                    return False

            return True
        except Exception as e:
            logger.error(f"이클래스 세션 유효성 검증 중 오류: {str(e)}")
            return False