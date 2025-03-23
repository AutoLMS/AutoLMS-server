import logging

from fastapi import HTTPException, status
from typing import Dict, Any
from supabase.lib.client_options import ClientOptions
from postgrest.exceptions import APIError

from app.core.config import settings
from app.core.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

class AuthService:
    """Supabase Auth 기반 인증 서비스"""

    def __init__(self, supabase_client=None):
        self.supabase = supabase_client or get_supabase_client()

    async def register(self, email: str, password: str) -> Dict[str, Any]:
        """새 사용자 등록"""
        try:
            auth_response = self.supabase.auth.sign_up({
                "email": email,
                "password": password
            })

            if auth_response.user:
                return {
                    "user": {
                        "id": auth_response.user.id,
                        "email": auth_response.user.email
                    }
                }
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="회원가입 처리 중 오류가 발생했습니다."
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """사용자 로그인"""
        try:
            auth_response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if auth_response.user and auth_response.session:
                return {
                    "session": {
                        "access_token": auth_response.session.access_token,
                        "refresh_token": auth_response.session.refresh_token
                    },
                    "user": {
                        "id": auth_response.user.id,
                        "email": auth_response.user.email
                    }
                }
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="로그인 처리 중 오류가 발생했습니다."
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )

    async def get_current_user(self, token: str) -> Dict[str, Any]:
        """토큰에서 현재 사용자 정보 추출"""
        try:
            logger.info(f"Received token: {token[:10]}...")  # 토큰의 앞부분만 로깅

            # JWT 형식 검증
            if not token or not token.count('.') == 2:
                logger.error("Invalid token format")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="유효하지 않은 토큰 형식입니다."
                )

            # 사용자 정보 조회 시도
            try:
                user_response = self.supabase.auth.get_user(token)
                logger.info(f"User response received: {user_response}")

                if not user_response or not user_response.user:
                    logger.error("No user data in response")
                    raise ValueError("사용자 정보를 찾을 수 없습니다.")

                # 사용자 정보 반환
                return {
                    "id": user_response.user.id,
                    "email": user_response.user.email,
                    "token": token
                }

            except Exception as supabase_error:
                logger.error(f"Supabase get_user error: {str(supabase_error)}")
                raise

        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"유효하지 않은 인증 정보입니다. Error: {str(e)}"
            )

    async def logout(self, token: str) -> Dict[str, Any]:
        """사용자 로그아웃"""
        try:
            # 이미 로그아웃된 상태인지 확인
            try:
                user = self.supabase.auth.get_user(token)
                if not user:
                    return {"status": "already_logged_out", "message": "이미 로그아웃된 상태입니다."}
            except Exception as e:
                # 토큰이 유효하지 않은 경우 - 이미 로그아웃되었거나 만료된 경우
                return {"status": "already_logged_out", "message": "이미 로그아웃된 상태입니다."}

            # Supabase의 sign_out 메서드를 모방하여 구현
            try:
                # access_token을 전달하여 서버 측 로그아웃 처리
                self.supabase.auth.admin.sign_out(token)
            except Exception:
                # 오류 무시 - Supabase도 AuthApiError를 무시함
                pass

            # 로컬 세션 제거
            # 클라이언트 측에서는 storage 관리가 필요하지만, 서버 측에서는 세션만 무효화하면 됨
            return {"status": "success", "message": "로그아웃되었습니다."}

        except Exception as e:
            # 예상치 못한 오류 처리
            # logging.error(f"로그아웃 처리 중 오류: {str(e)}")
            raise Exception(f"로그아웃 처리 중 오류가 발생했습니다: {str(e)}")