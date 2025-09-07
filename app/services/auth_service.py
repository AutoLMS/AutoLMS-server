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
        """eClass 계정으로 회원가입 (Supabase Auth 활용)"""
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
            
            # 3. 중복 사용자 확인 (user_profiles에서 확인)
            from supabase import create_client
            service_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
            
            existing_profile = service_client.table('user_profiles')\
                .select('*')\
                .eq('autolms_id', autolms_id)\
                .execute()
            
            if existing_profile.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 등록된 사용자입니다."
                )
            
            # 4. Supabase Auth에 계정 생성
            auth_response = self.supabase.auth.sign_up({
                "email": virtual_email,
                "password": eclass_password
            })

            if not auth_response.user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="회원가입 처리 중 오류가 발생했습니다."
                )

            # 5. user_profiles에 eClass 정보 저장 (비밀번호 암호화)
            try:
                encryption_service = get_encryption_service()
                encrypted_password = encryption_service.encrypt_password(eclass_password)
                
                profile_data = {
                    "user_id": auth_response.user.id,
                    "autolms_id": autolms_id,
                    "eclass_username": eclass_username,
                    "eclass_password": encrypted_password,
                    "eclass_session_token": await eclass_service.get_session_token() or ""
                }
                
                service_client.table('user_profiles').insert(profile_data).execute()
                
                print(f"✅ user_profiles 생성 성공: {autolms_id}")
                
            except Exception as e:
                print(f"❌ user_profiles 생성 실패: {e}")
                # Auth 계정은 생성되었으므로 계속 진행
            
            # 6. 응답 생성
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
        """eClass 계정으로 로그인 (Supabase Auth 활용)"""
        try:
            # 1. eClass 로그인 먼저 검증
            eclass_service = EclassService()
            eclass_login_success = await eclass_service.login(eclass_username, eclass_password)
            
            if not eclass_login_success:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="eClass 로그인 정보가 올바르지 않습니다."
                )
            
            # 2. 가상 이메일로 Supabase Auth 로그인 시도
            virtual_email = f"seoultech_{eclass_username}@autolms.internal"
            
            try:
                auth_response = self.supabase.auth.sign_in_with_password({
                    "email": virtual_email,
                    "password": eclass_password
                })
            except Exception as e:
                # Supabase Auth 계정이 없으면 자동으로 생성
                print(f"Supabase Auth 로그인 실패, 계정 자동 생성: {e}")
                return await self.eclass_register(eclass_username, eclass_password)

            if not auth_response.user or not auth_response.session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="로그인 정보가 올바르지 않습니다."
                )

            # 2. user_profiles에서 추가 정보 조회 및 생성
            try:
                profile_response = self.supabase.table('user_profiles')\
                    .select('*')\
                    .eq('user_id', auth_response.user.id)\
                    .execute()
                
                if profile_response.data and len(profile_response.data) > 0:
                    profile_data = profile_response.data[0]
                else:
                    # user_profiles에 데이터가 없으면 생성
                    print(f"user_profiles 데이터가 없습니다. 자동 생성 중...")
                    autolms_id = f"seoultech_{eclass_username}"
                    
                    # Service key 클라이언트로 생성 (RLS 우회)
                    from supabase import create_client
                    service_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
                    
                    new_profile = {
                        "user_id": auth_response.user.id,
                        "autolms_id": autolms_id,
                        "eclass_username": eclass_username,
                        "eclass_session_token": ""
                    }
                    
                    service_client.table('user_profiles').insert(new_profile).execute()
                    profile_data = new_profile
                    print(f"✅ user_profiles 자동 생성 완료: {autolms_id}")
                
            except Exception as e:
                print(f"Warning: Could not fetch/create user profile: {e}")
                profile_data = {"autolms_id": f"seoultech_{eclass_username}", "eclass_username": eclass_username}

            # 3. eClass 세션 토큰 업데이트 (optional)
            try:
                # eClass 세션 토큰은 나중에 필요할 때 업데이트하도록 함
                pass
            except Exception as e:
                print(f"Warning: Could not update eClass session: {e}")

            # 4. 응답 생성
            return {
                "access_token": auth_response.session.access_token,
                "token_type": "bearer",
                "user": {
                    "id": auth_response.user.id,
                    "username": profile_data.get("autolms_id", f"seoultech_{eclass_username}"),
                    "eclass_username": profile_data.get("eclass_username", eclass_username),
                    "created_at": str(auth_response.user.created_at) if auth_response.user.created_at else ""
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"로그인 처리 중 오류가 발생했습니다: {str(e)}"
            )

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
            
            # user_profiles에서 추가 정보 가져오기
            try:
                profile_response = self.supabase.table('user_profiles')\
                    .select('*')\
                    .eq('user_id', user.id)\
                    .execute()
                
                if profile_response.data and len(profile_response.data) > 0:
                    profile_data = profile_response.data[0]
                else:
                    profile_data = {}
                
            except Exception as e:
                print(f"Warning: Could not fetch user profile: {e}")
                profile_data = {}

            return {
                "id": user.id,
                "username": profile_data.get("autolms_id", ""),
                "eclass_username": profile_data.get("eclass_username", ""),
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
        """사용자의 e-Class 로그인 정보 조회"""
        try:
            # Service Key를 사용하여 user_profiles에서 정보 조회
            from supabase import create_client
            service_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
            
            profile_response = service_client.table('user_profiles')\
                .select('eclass_username, eclass_password')\
                .eq('user_id', user_id)\
                .single()\
                .execute()
            
            if profile_response.data:
                eclass_username = profile_response.data.get("eclass_username")
                encrypted_password = profile_response.data.get("eclass_password")
                
                if eclass_username and encrypted_password:
                    # 암호화된 비밀번호 복호화
                    encryption_service = get_encryption_service()
                    
                    # 이미 암호화된 비밀번호인지 확인
                    if encryption_service.is_encrypted(encrypted_password):
                        decrypted_password = encryption_service.decrypt_password(encrypted_password)
                    else:
                        # 평문 비밀번호인 경우 (기존 데이터 호환성)
                        decrypted_password = encrypted_password
                        
                        # 평문을 암호화해서 다시 저장
                        new_encrypted = encryption_service.encrypt_password(encrypted_password)
                        service_client.table('user_profiles')\
                            .update({'eclass_password': new_encrypted})\
                            .eq('user_id', user_id)\
                            .execute()
                        print(f"🔐 기존 평문 비밀번호를 암호화했습니다: {eclass_username}")
                    
                    return {
                        "eclass_username": eclass_username,
                        "eclass_password": decrypted_password
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