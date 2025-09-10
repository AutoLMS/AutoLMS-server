"""
Supabase JWT 기반 단순화된 인증 세션 서비스

기존의 복잡한 PostgreSQL 세션 관리를 제거하고,
Supabase JWT 토큰 검증만 담당하는 경량화된 서비스로 리팩토링
"""

import logging
from typing import Dict, Optional, Any
from fastapi import HTTPException, status

from app.core.supabase_client import get_supabase_client
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)


class AuthSessionService(BaseService):
    """Supabase JWT 기반 단순화된 인증 세션 서비스"""

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.supabase = get_supabase_client()
            self._initialized = True
            logger.info("AuthSessionService 초기화 완료")

    async def initialize(self) -> None:
        """서비스 초기화"""
        logger.info("AuthSessionService 시작")
        pass

    async def close(self) -> None:
        """서비스 종료 및 리소스 정리"""
        logger.info("AuthSessionService 종료")
        pass

    async def create_session(self, user_id: str, eclass_username: str = None) -> Dict[str, Any]:
        """
        세션 생성 - 실제로는 이미 생성된 Supabase JWT를 사용하므로 더 이상 필요 없음
        AuthService에서 직접 Supabase JWT를 반환하도록 변경됨
        
        이 메서드는 기존 호환성을 위해 유지하되, 경고를 출력
        """
        logger.warning("create_session은 더 이상 사용되지 않습니다. AuthService에서 직접 Supabase JWT를 사용하세요.")
        return {
            "message": "Use AuthService.register() or AuthService.login() directly for JWT tokens"
        }

    async def end_session(self, token: str) -> bool:
        """
        세션 종료 - Supabase Auth로 위임
        실제 로그아웃은 AuthService.logout()에서 처리
        """
        try:
            # Supabase 토큰 유효성 확인만 수행
            user_response = self.supabase.auth.get_user(token)
            if user_response and user_response.user:
                logger.info("유효한 세션 종료 요청")
                return True
            else:
                logger.info("이미 만료된 세션")
                return False
        except Exception as e:
            logger.error(f"세션 종료 중 오류: {str(e)}")
            return False

    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        JWT 토큰 검증 및 사용자 정보 반환
        
        Args:
            token: Supabase JWT 토큰
            
        Returns:
            Dict: 사용자 정보 또는 None
        """
        try:
            logger.debug("토큰 검증 시작")
            
            # Supabase JWT 토큰 검증
            user_response = self.supabase.auth.get_user(token)
            
            if not user_response or not user_response.user:
                logger.warning("유효하지 않은 토큰")
                return None
            
            user_id = user_response.user.id
            
            # Supabase users 테이블에서 eclass_username 조회
            try:
                user_data_response = self.supabase.table('users').select('eclass_username').eq('id', user_id).execute()
                eclass_username = user_data_response.data[0]['eclass_username'] if user_data_response.data else None
            except Exception as e:
                logger.warning(f"eclass_username 조회 실패: {str(e)}")
                eclass_username = None
            
            user_info = {
                "id": user_id,
                "eclass_username": eclass_username,
                "email": user_response.user.email
            }
            
            logger.debug(f"토큰 검증 성공: 사용자 {user_id}")
            return user_info
            
        except Exception as e:
            logger.error(f"토큰 검증 중 오류: {str(e)}")
            return None

    async def get_current_user_from_token(self, token: str) -> Dict[str, Any]:
        """
        토큰에서 현재 사용자 정보 추출 (HTTP 예외 포함)
        
        Args:
            token: Supabase JWT 토큰
            
        Returns:
            Dict: 사용자 정보
            
        Raises:
            HTTPException: 토큰이 유효하지 않은 경우
        """
        user_info = await self.verify_token(token)
        
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 인증 토큰입니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user_info

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        리프레시 토큰으로 새로운 액세스 토큰 발급
        
        Args:
            refresh_token: Supabase 리프레시 토큰
            
        Returns:
            Dict: 새로운 토큰 정보
            
        Raises:
            HTTPException: 리프레시 실패 시
        """
        try:
            # Supabase Auth의 토큰 갱신 기능 사용
            refresh_response = self.supabase.auth.refresh_session(refresh_token)
            
            if not refresh_response or not refresh_response.session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="리프레시 토큰이 유효하지 않습니다."
                )
            
            logger.info("토큰 갱신 성공")
            return {
                "access_token": refresh_response.session.access_token,
                "refresh_token": refresh_response.session.refresh_token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            logger.error(f"토큰 갱신 중 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="토큰 갱신에 실패했습니다."
            )