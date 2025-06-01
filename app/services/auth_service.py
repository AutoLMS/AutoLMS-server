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

    async def register(self, email: str, password: str, eclass_username: str, eclass_password: str) -> Dict[str, Any]:
        """새 사용자 등록"""
        try:
            # Supabase Auth에 사용자 등록
            auth_response = self.supabase.auth.sign_up({
                "email": email,
                "password": password
            })

            if auth_response.user:
                # user_details 테이블에 e-Class 정보 저장
                try:
                    user_details_response = self.supabase.table('user_details').insert({
                        "user_id": auth_response.user.id,
                        "eclass_username": eclass_username,
                        "eclass_password": eclass_password
                    }).execute()
                    
                except Exception as e:
                    # Auth에서 사용자는 생성되었지만 user_details 저장 실패
                    # 이 경우 rollback이 어려우므로 경고만 로그
                    print(f"Warning: User created but eclass details failed to save: {e}")
                
                return {
                    "user": {
                        "id": auth_response.user.id,
                        "email": auth_response.user.email,
                        "eclass_username": eclass_username
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
            # 개발 환경에서 테스트 계정은 이메일 확인 없이 가짜 토큰 생성
            if settings.ENVIRONMENT == "development" and email.startswith("devtest"):
                # 간단한 가짜 토큰과 사용자 정보 반환
                fake_user_id = "1ae6fcaa-c18d-40a7-83bb-56715689b47c"  # 등록된 사용자 ID
                fake_token = f"dev_token_{fake_user_id}"
                
                return {
                    "session": {
                        "access_token": fake_token,
                        "refresh_token": fake_token
                    },
                    "user": {
                        "id": fake_user_id,
                        "email": email
                    }
                }
            
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
            error_message = str(e)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_message
            )

    async def get_current_user(self, token: str) -> Dict[str, Any]:
        """토큰에서 현재 사용자 정보 추출"""
        try:
            # 개발 환경에서 가짜 토큰 처리
            if settings.ENVIRONMENT == "development" and token.startswith("dev_token_"):
                user_id = token.replace("dev_token_",
                                        "")
                return {
                    "id": user_id,
                    "email": "devtest@gmail.com",
                    "token": token
                }
            
            # Supabase 클라이언트의 세션 관리 활용
            self.supabase.auth.set_session(token, token)  # access_token과 refresh_token 설정
            user = self.supabase.auth.get_user()

            if user and user.user:  # user 객체가 있고 user 정보가 있는지 확인
                user_data = {
                    "id": user.user.id,
                    "email": user.user.email,
                    "token": token
                }
                
                # user_details에서 e-Class 정보 가져오기
                try:
                    details_response = self.supabase.table('user_details').select('eclass_username').eq('user_id', user.user.id).execute()
                    if details_response.data:
                        user_data["eclass_username"] = details_response.data[0].get("eclass_username")
                except Exception as e:
                    # e-Class 정보가 없어도 기본 사용자 정보는 반환
                    print(f"Warning: Could not fetch eclass details: {e}")
                
                return user_data

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 인증 정보입니다."
            )

        except HTTPException:
            # HTTPException은 그대로 전달
            raise
        except Exception as e:
            # 구체적인 에러 메시지 포함
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"인증 처리 중 오류가 발생했습니다: {str(e)}"
            )
    
    async def get_user_eclass_credentials(self, user_id: str) -> Dict[str, str]:
        """사용자의 e-Class 로그인 정보 조회"""
        try:
            details_response = self.supabase.table('user_details').select('eclass_username, eclass_password').eq('user_id', user_id).execute()
            if details_response.data:
                return {
                    "eclass_username": details_response.data[0].get("eclass_username"),
                    "eclass_password": details_response.data[0].get("eclass_password")
                }
            else:
                # Fallback to environment variables (기존 방식)
                return {
                    "eclass_username": settings.ECLASS_USERNAME,
                    "eclass_password": settings.ECLASS_PASSWORD
                }
        except Exception as e:
            print(f"Warning: Could not fetch eclass credentials: {e}")
            # Fallback to environment variables
            return {
                "eclass_username": settings.ECLASS_USERNAME,
                "eclass_password": settings.ECLASS_PASSWORD
            }

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