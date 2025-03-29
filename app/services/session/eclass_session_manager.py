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

    async def get_session(self, user_id: str) -> Optional[EclassSession]:
        """
        사용자를 위한 이클래스 세션 가져오기

        Args:
            user_id: 사용자 ID

        Returns:
            Optional[EclassSession]: 이클래스 세션 또는 None
        """
        lock = await self._ensure_lock()
        async with lock:
            # 기존 세션 확인
            if user_id in self.eclass_sessions:
                session = self.eclass_sessions[user_id]
                is_logged_in = await session.is_logged_in()

                if is_logged_in:
                    logger.debug(f"사용자 {user_id}의 기존 세션 재사용")
                    return session
                else:
                    logger.debug(f"사용자 {user_id}의 세션이 만료됨, 새로운 세션 생성")

            # 사용자의 이클래스 계정 정보 조회
            eclass_credentials = await self._get_user_eclass_credentials(user_id)
            if not eclass_credentials:
                logger.error(f"사용자 {user_id}의 이클래스 계정 정보를 찾을 수 없음")
                return None

            # 새 세션 생성 및 로그인
            eclass_session = EclassSession()

            # 로그인 시 이클래스 학번/비밀번호 사용
            login_success = await eclass_session.login(
                username=eclass_credentials["username"],
                password=eclass_credentials["password"]
            )

            if login_success:
                logger.info(f"사용자 {user_id} 로그인 성공")
                # 세션 객체에 이클래스 ID 저장 (URL 생성 시 사용)
                eclass_session.eclass_id = eclass_credentials["username"]
                self.eclass_sessions[user_id] = eclass_session
                return eclass_session
            else:
                logger.error(f"사용자 {user_id} 로그인 실패")
                return None

    async def _get_user_eclass_credentials(self, user_id: str) -> Optional[Dict[str, str]]:
        """
        사용자의 이클래스 계정 정보 조회

        Args:
            user_id: 사용자 ID

        Returns:
            Optional[Dict[str, str]]: 이클래스 계정 정보 또는 None
        """
        try:
            # Supabase에서 사용자 정보 조회
            from app.core.supabase_client import get_supabase_client

            supabase = get_supabase_client()
            response = supabase.table('users').select('eclass_username, eclass_password').eq('id', user_id).execute()

            if response.data and len(response.data) > 0:
                user_data = response.data[0]
                return {
                    "username": user_data["eclass_username"],
                    "password": user_data["eclass_password"]  # 실제로는 복호화 필요
                }

            # 환경 변수의 기본 계정 정보 사용 (공통 계정)
            # 참고: 이는 임시 대안이며, 이상적으로는 각 사용자가 자신의 계정을 사용해야 함
            from app.core.config import settings
            if settings.ECLASS_USERNAME and settings.ECLASS_PASSWORD:
                logger.warning(f"사용자 {user_id}의 이클래스 계정 정보가 없어 기본 계정 사용")
                return {
                    "username": settings.ECLASS_USERNAME,
                    "password": settings.ECLASS_PASSWORD
                }

            return None
        except Exception as e:
            logger.error(f"이클래스 계정 정보 조회 중 오류: {str(e)}")
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
