import asyncio
from fastapi import HTTPException, status
from typing import Dict, Any
from supabase.lib.client_options import ClientOptions
from postgrest.exceptions import APIError

from app.core.config import settings
from app.core.supabase_client import get_supabase_client
from app.services.eclass_service import EclassService
from app.services.encryption_service import get_encryption_service


class AuthService:
    """Supabase Auth + eClass 통합 인증 서비스"""

    def __init__(self, supabase_client=None):
        self.supabase = supabase_client or get_supabase_client()

    async def eclass_register(self, eclass_username: str, eclass_password: str) -> Dict[str, Any]:
        """eClass 계정으로 회원가입 (Supabase Auth + user_metadata 활용)"""
        try:
            # 1. eClass 로그인 검증
            eclass_service = EclassService()
            login_success = await eclass_service.login(eclass_username, eclass_password)
            
            if not login_success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="eClass 로그인 정보가 올바르지 않습니다."
                )
            
            # 2. 가상 이메일 및 AutoLMS ID 생성
            virtual_email = f"seoultech_{eclass_username}@autolms.internal"
            autolms_id = f"seoultech_{eclass_username}"
            
            # 3. eClass 비밀번호 암호화
            from app.services.encryption_service import get_encryption_service
            encryption_service = get_encryption_service()
            encrypted_password = encryption_service.encrypt_password(eclass_password)
            
            # 4. Supabase Auth에 계정 생성 (user_metadata에 eClass 정보 저장)
            fixed_password = f"autolms_{eclass_username}_2024"
            
            try:
                # 비동기 래핑으로 블로킹 방지
                auth_response = await asyncio.to_thread(
                    self.supabase.auth.sign_up,
                    {
                        "email": virtual_email,
                        "password": fixed_password,
                        "options": {
                            "data": {
                                "autolms_id": autolms_id,
                                "eclass_username": eclass_username,
                                "eclass_password": encrypted_password
                            }
                        }
                    }
                )
            except Exception as e:
                error_msg = str(e).lower()
                if "user already registered" in error_msg or "already registered" in error_msg:
                    # 이미 존재하는 사용자의 경우 로그인으로 처리
                    print(f"🔄 기존 사용자 감지, 로그인으로 전환: {eclass_username}")
                    return await self.eclass_login(eclass_username, eclass_password)
                else:
                    # 다른 에러는 그대로 전파
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"회원가입 처리 중 오류가 발생했습니다: {str(e)}"
                    )

            if not auth_response.user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="회원가입 처리 중 오류가 발생했습니다."
                )
            
            # 5. 응답 생성
            return {
                "access_token": auth_response.session.access_token if auth_response.session else "",
                "token_type": "bearer",
                "user": {
                    "id": auth_response.user.id,
                    "username": autolms_id,
                    "eclass_username": eclass_username,
                    "created_at": str(auth_response.user.created_at) if auth_response.user.created_at else ""
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"회원가입 처리 중 오류가 발생했습니다: {str(e)}"
            )
    
    async def eclass_login(self, eclass_username: str, eclass_password: str) -> Dict[str, Any]:
        """eClass 계정으로 로그인 (user_metadata 기반, 무한재귀 방지)"""
        try:
            # 1. eClass 로그인 검증
            eclass_service = EclassService()
            eclass_login_success = await eclass_service.login(eclass_username, eclass_password)
            
            if not eclass_login_success:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="eClass 로그인 정보가 올바르지 않습니다."
                )
            
            # 2. 가상 이메일 생성
            virtual_email = f"seoultech_{eclass_username}@autolms.internal"
            fixed_password = f"autolms_{eclass_username}_2024"
            
            # 3. Supabase Auth 로그인 시도
            try:
                auth_response = await asyncio.to_thread(
                    self.supabase.auth.sign_in_with_password,
                    {
                        "email": virtual_email,
                        "password": fixed_password
                    }
                )
                
                if auth_response.user and auth_response.session:
                    # 로그인 성공 - user_metadata에서 정보 가져오기
                    user_metadata = auth_response.user.user_metadata or {}
                    autolms_id = user_metadata.get("autolms_id", f"seoultech_{eclass_username}")
                    
                    # 비밀번호가 변경되었는지 확인하고 user_metadata 업데이트
                    await self._update_user_metadata_if_needed(
                        auth_response.user.id, eclass_username, eclass_password, user_metadata
                    )
                    
                    return {
                        "access_token": auth_response.session.access_token,
                        "token_type": "bearer",
                        "user": {
                            "id": auth_response.user.id,
                            "username": autolms_id,
                            "eclass_username": eclass_username,
                            "created_at": str(auth_response.user.created_at) if auth_response.user.created_at else ""
                        }
                    }
                
            except Exception as auth_error:
                error_msg = str(auth_error).lower()
                if "invalid login credentials" in error_msg:
                    # Auth 계정이 없는 경우 - 회원가입으로 처리 (단, 재귀 방지)
                    print(f"🔄 미등록 사용자, 회원가입 진행: {eclass_username}")
                    return await self.eclass_register(eclass_username, eclass_password)
                else:
                    # 다른 Auth 에러
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=f"로그인 처리 중 오류: {str(auth_error)}"
                    )
            
            # 여기까지 오면 예상치 못한 상황
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="로그인 처리 중 예상치 못한 오류가 발생했습니다."
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"로그인 처리 중 오류가 발생했습니다: {str(e)}"
            )
            
    async def _update_user_metadata_if_needed(self, user_id: str, eclass_username: str, 
                                            eclass_password: str, current_metadata: dict) -> None:
        """필요시 user_metadata의 eClass 비밀번호 업데이트"""
        try:
            from app.services.encryption_service import get_encryption_service
            encryption_service = get_encryption_service()
            
            stored_encrypted = current_metadata.get("eclass_password", "")
            if stored_encrypted:
                # 저장된 비밀번호와 현재 비밀번호 비교
                if encryption_service.is_encrypted(stored_encrypted):
                    decrypted_stored = encryption_service.decrypt_password(stored_encrypted)
                else:
                    decrypted_stored = stored_encrypted
                
                if decrypted_stored != eclass_password:
                    # 비밀번호가 변경됨 - metadata 업데이트
                    print(f"🔐 비밀번호 변경 감지, user_metadata 업데이트: {eclass_username}")
                    new_encrypted = encryption_service.encrypt_password(eclass_password)
                    
                    updated_metadata = current_metadata.copy()
                    updated_metadata["eclass_password"] = new_encrypted
                    
                    # user_metadata 업데이트
                    await asyncio.to_thread(
                        self.supabase.auth.admin.update_user_by_id,
                        user_id,
                        {"user_metadata": updated_metadata}
                    )
                    
        except Exception as e:
            print(f"Warning: user_metadata 업데이트 실패: {e}")
            # 메타데이터 업데이트 실패해도 로그인은 계속 진행

    async def _perform_login(self, profile_data: Dict[str, Any], eclass_username: str, eclass_password: str) -> Dict[str, Any]:
        """실제 Supabase Auth 로그인 수행 (더 이상 사용되지 않음 - 호환성 유지)"""
        # 이 함수는 더 이상 사용되지 않지만 호환성을 위해 유지
        # 새로운 로직은 eclass_login에서 직접 처리
        return await self.eclass_login(eclass_username, eclass_password)

    async def get_current_user(self, token: str) -> Dict[str, Any]:
        """현재 사용자 정보 조회 (Supabase Auth 기반)"""
        try:
            # JWT 토큰 직접 검증
            user_response = self.supabase.auth.get_user(jwt=token)

            if not user_response or not user_response.user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="유효하지 않은 인증 정보입니다."
                )

            user = user_response.user
            
            # 세션 설정 (RLS 정책을 위해 필요)
            self.supabase.auth.set_session(access_token=token, refresh_token="")
            
            # user_metadata에서 정보 가져오기
            user_metadata = user.user_metadata or {}

            return {
                "id": user.id,
                "username": user_metadata.get("autolms_id", ""),
                "eclass_username": user_metadata.get("eclass_username", ""),
                "email": user.email,
                "created_at": user.created_at,
                "token": token
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"인증 처리 중 오류가 발생했습니다: {str(e)}"
            )
    
    async def get_user_eclass_credentials(self, user_id: str) -> Dict[str, str]:
        """사용자의 e-Class 로그인 정보 조회 (user_metadata 기반)"""
        try:
            # Service Key를 사용하여 사용자 정보 조회
            from supabase import create_client
            service_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
            
            # Admin API로 사용자 정보 조회
            user_response = await asyncio.to_thread(
                service_client.auth.admin.get_user_by_id,
                user_id
            )
            
            if user_response and user_response.user:
                user_metadata = user_response.user.user_metadata or {}
                eclass_username = user_metadata.get("eclass_username")
                eclass_password = user_metadata.get("eclass_password")
                
                if eclass_username and eclass_password:
                    return {
                        "eclass_username": eclass_username,
                        "eclass_password": eclass_password
                    }
            
            # 데이터를 찾을 수 없으면 오류 발생
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="사용자의 eClass 로그인 정보를 찾을 수 없습니다."
            )
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"Warning: Could not fetch eclass credentials: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="eClass 로그인 정보 조회 중 오류가 발생했습니다."
            )

    async def logout(self, token: str) -> Dict[str, Any]:
        """사용자 로그아웃"""
        try:
            # Supabase Auth 로그아웃
            self.supabase.auth.set_session(token, token)
            self.supabase.auth.sign_out()
            
            return {"status": "success", "message": "로그아웃되었습니다."}

        except Exception as e:
            # 예상치 못한 오류 처리
            print(f"로그아웃 처리 중 오류: {str(e)}")
            return {"status": "success", "message": "로그아웃되었습니다."}  # 로그아웃은 항상 성공으로 처리