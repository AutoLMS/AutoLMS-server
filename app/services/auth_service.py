from fastapi import HTTPException, status
from typing import Dict, Any
from supabase.lib.client_options import ClientOptions
from postgrest.exceptions import APIError

from app.core.config import settings
from app.core.supabase_client import get_supabase_client


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
            # 토큰 검증 및 사용자 정보 조회
            # self.supabase.auth.set_session(token, None)
            # user = self.supabase.auth.get_user()
            user = self.supabase.auth.get_user(token)

            if user:
                return {
                    "id": user.id,
                    "email": user.email,
                    "token": token  # 토큰 정보 추가
                }
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 인증 정보입니다."
            )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="인증 처리 중 오류가 발생했습니다."
            )

    async def logout(self, token: str) -> Dict[str, Any]:
        """사용자 로그아웃"""
        try:
            # 세션 설정 및 로그아웃
            self.supabase.auth.set_session(token, None)
            self.supabase.auth.sign_out()
            return {"message": "로그아웃되었습니다."}

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"로그아웃 처리 중 오류가 발생했습니다: {str(e)}"
            )