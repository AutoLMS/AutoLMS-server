import asyncio
import logging
from typing import Dict, Optional, Any
from datetime import datetime

from app.services.eclass_session import EclassSession
from app.core.config import settings
from app.services.base_service import BaseService

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
            self.eclass_sessions: Dict[str, EclassSession] = {}  # user_id -> EclassSession
            self.lock = asyncio.Lock()
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
    
    async def get_session(self, user_id: str, username: str = None, password: str = None) -> Optional[EclassSession]:
        """사용자를 위한 이클래스 세션 가져오기 (필요시 생성)"""
        async with self.lock:
            # 기존 세션이 있고 유효하면 재사용
            if user_id in self.eclass_sessions:
                session = self.eclass_sessions[user_id]
                if await session.is_logged_in():
                    logger.debug(f"사용자 {user_id}의 기존 세션 재사용")
                    return session
                else:
                    logger.debug(f"사용자 {user_id}의 세션이 만료됨, 새로운 세션 생성")
            
            # 자격 증명 확인
            if not username or not password:
                # 설정에서 기본 자격 증명 사용
                username = settings.ECLASS_USERNAME
                password = settings.ECLASS_PASSWORD
                
                if not username or not password:
                    logger.error("자격 증명이 제공되지 않았고 기본값도 설정되지 않음")
                    return None
            
            # 새 세션 생성 및 로그인
            eclass_session = EclassSession()
            login_success = await eclass_session.login(username=username, password=password)
            
            if login_success:
                logger.info(f"사용자 {user_id} 로그인 성공")
                self.eclass_sessions[user_id] = eclass_session
                return eclass_session
            else:
                logger.error(f"사용자 {user_id} 로그인 실패")
                return None
    
    async def invalidate_session(self, user_id: str) -> None:
        """사용자 세션 무효화"""
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
                    if not await session.is_logged_in():
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
            logger.info("모든 세션 종료 완료")
