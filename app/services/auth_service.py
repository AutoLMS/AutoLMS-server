import logging

from fastapi import HTTPException, status
from typing import Dict, Any, Optional
from supabase.lib.client_options import ClientOptions
from postgrest.exceptions import APIError
import traceback
from datetime import datetime

from app.core.config import settings
from app.core.supabase_client import get_supabase_client
from app.utils.encryption import encrypt_eclass_password, decrypt_eclass_password, is_encrypted
from app.db.repositories.user_repository import UserRepository
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

class AuthService:
    """Supabase Auth 기반 인증 서비스"""

    def __init__(self, supabase_client=None):
        self.supabase = supabase_client or get_supabase_client()
        self.user_repository = UserRepository()

    # app/services/auth_service.py


    logger = logging.getLogger(__name__)

    async def register(self, eclass_username: str, eclass_password: str) -> Dict[str, Any]:
        """새 사용자 등록 - 이클래스 계정만으로 가입"""
        try:
            # 먼저 이클래스 계정 검증
            is_valid = await self.validate_eclass_credentials(eclass_username, eclass_password)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이클래스 계정 정보가 유효하지 않습니다."
                )

            # 자동으로 이메일과 패스워드 생성 (eclass_username을 비밀번호로 사용)
            auto_email = f"seoultech@{eclass_username}"
            auto_password = eclass_username  # eclass_username을 Supabase 비밀번호로 사용
            
            logger.info(f"사용자 등록 시작: 이클래스 계정 {eclass_username} -> 자동 이메일 {auto_email}")

            # Supabase Auth로 사용자 등록
            auth_response = self.supabase.auth.sign_up({
                "email": auto_email,
                "password": auto_password
            })

            logger.info(f"Supabase Auth 등록 응답: {auth_response}")

            if auth_response.user:
                user_id = auth_response.user.id
                logger.info(f"사용자 등록 성공, ID: {user_id}")

                # 사용자 메타데이터 저장
                try:
                    logger.info(f"사용자 메타데이터 저장 시작: {user_id}")

                    # 저장할 사용자 데이터 구성 (이클래스 비밀번호 암호화)
                    encrypted_eclass_password = encrypt_eclass_password(eclass_password)
                    user_data = {
                        'id': user_id,
                        'eclass_username': eclass_username,
                        'encrypted_session_token': encrypted_eclass_password,  # AES-256 암호화됨 (임시로 이 컬럼 사용)
                        'created_at': datetime.now().isoformat()
                    }

                    logger.debug(f"저장할 사용자 데이터: {user_data}")

                    # Supabase 테이블 확인
                    try:
                        # 테이블 존재 여부 확인
                        table_query = self.supabase.table('users').select('count').limit(1)
                        table_result = table_query.execute()
                        logger.debug(f"테이블 확인 결과: {table_result}")
                    except Exception as table_error:
                        logger.error(f"테이블 확인 중 오류: {str(table_error)}")

                    # 데이터 삽입 시도
                    insert_result = self.supabase.table('users').insert(user_data).execute()
                    logger.info(f"사용자 메타데이터 저장 성공: {insert_result}")

                except Exception as metadata_error:
                    error_traceback = traceback.format_exc()
                    logger.error(f"사용자 메타데이터 저장 중 오류: {str(metadata_error)}")
                    logger.error(f"상세 오류 정보: {error_traceback}")

                    # 오류 정보를 보다 자세히 로깅
                    if hasattr(metadata_error, 'response'):
                        logger.error(
                            f"API 응답 오류: {metadata_error.response.text if hasattr(metadata_error.response, 'text') else 'No response text'}")

                    # 사용자는 생성되었지만 메타데이터 저장에 실패한 경우 처리
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"사용자 계정이 생성되었지만 이클래스 계정 정보 저장에 실패했습니다. 오류: {str(metadata_error)}"
                    )

                # Supabase JWT 토큰 포함하여 반환
                return {
                    "access_token": auth_response.session.access_token if auth_response.session else None,
                    "refresh_token": auth_response.session.refresh_token if auth_response.session else None,
                    "user": {
                        "id": user_id,
                        "eclass_username": eclass_username
                    }
                }
            else:
                logger.warning("Supabase 사용자 등록 응답에 사용자 정보가 없음")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="회원가입 처리 중 오류가 발생했습니다: 사용자 정보 누락"
                )

        except HTTPException as http_ex:
            # 이미 HTTPException인 경우 그대로 전달
            logger.error(f"HTTP 예외 발생: {http_ex.detail}")
            raise
        except Exception as e:
            error_traceback = traceback.format_exc()
            logger.error(f"사용자 등록 중 예외 발생: {str(e)}")
            logger.error(f"상세 예외 정보: {error_traceback}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"회원가입 처리 중 오류가 발생했습니다: {str(e)}"
            )

    async def login(self, eclass_username: str, eclass_password: str) -> Dict[str, Any]:
        """사용자 로그인 - 이클래스 계정으로 로그인"""
        try:
            # 먼저 이클래스 계정 검증
            is_valid = await self.validate_eclass_credentials(eclass_username, eclass_password)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="이클래스 계정 정보가 올바르지 않습니다."
                )

            # Supabase Auth 로그인 시도
            auto_email = f"seoultech@{eclass_username}"
            auto_password = eclass_username  # eclass_username을 비밀번호로 사용
            
            try:
                # Supabase Auth로 로그인
                logger.info("Supabase 로그인 시도")
                auth_response = self.supabase.auth.sign_in_with_password({
                    "email": auto_email,
                    "password": auto_password
                })
                
                if not auth_response.user or not auth_response.session:
                    logger.error("Supabase 인증 응답에 사용자나 세션 정보 없음")
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="등록되지 않은 이클래스 계정입니다. 먼저 회원가입을 진행해주세요."
                    )
                
                user_id = auth_response.user.id
                access_token = auth_response.session.access_token
                refresh_token = auth_response.session.refresh_token
                
                
                # 이클래스 비밀번호 업데이트 (암호화된 상태로)
                await self._update_eclass_password(user_id, eclass_password)
                
                # 로컬 데이터베이스에 사용자 정보 동기화
                await self.sync_user_to_local_db(user_id, eclass_username, auth_response.user.email)
                
                # Supabase JWT 토큰 반환
                result = {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": {
                        "id": user_id,
                        "eclass_username": eclass_username
                    }
                }
                
                logger.info(f"로그인 결과 반환: access_token 길이={len(access_token)}, user_id={user_id}")
                return result
                
            except Exception as auth_error:
                logger.error(f"Supabase 인증 중 오류: {str(auth_error)}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="로그인 처리 중 오류가 발생했습니다. 회원가입이 필요할 수 있습니다."
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"로그인 처리 중 예외 발생: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="로그인 처리 중 오류가 발생했습니다."
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

            # AuthSessionService와 동일한 방식으로 토큰 검증
            user_id = None
            
            # 방법 1: 세션 설정 후 사용자 정보 조회
            try:
                # 토큰으로 세션 설정 
                self.supabase.auth.set_session(token, refresh_token="")
                
                # 현재 세션의 사용자 정보 조회
                user_response = self.supabase.auth.get_user()
                
                if user_response and user_response.user:
                    user_id = user_response.user.id
                    logger.info(f"세션 방식으로 사용자 ID 확인: {user_id}")
                    
            except Exception as session_error:
                logger.debug(f"세션 설정 방식 실패, JWT 파싱 시도: {str(session_error)}")
                
                # 방법 2: JWT 토큰 직접 파싱 (백업 방법)
                try:
                    import jwt
                    # JWT 토큰 디코드 (서명 검증 없이, 페이로드만 추출)
                    decoded_payload = jwt.decode(token, options={"verify_signature": False})
                    user_id = decoded_payload.get('sub')  # 'sub' 클레임이 사용자 ID
                    
                    if user_id:
                        logger.info(f"JWT 파싱으로 사용자 ID 추출: {user_id}")
                    else:
                        logger.error("JWT 토큰에 사용자 ID가 없음")
                        raise ValueError("JWT 토큰에 사용자 ID가 없습니다.")
                        
                except Exception as jwt_error:
                    logger.error(f"JWT 토큰 파싱 실패: {str(jwt_error)}")
                    raise ValueError(f"JWT 토큰 파싱 실패: {str(jwt_error)}")
            
            if not user_id:
                logger.error("사용자 ID를 확인할 수 없음")
                raise ValueError("사용자 정보를 찾을 수 없습니다.")

            # 사용자 정보 반환 (이클래스 유저명 포함)
            try:
                user_data_response = self.supabase.table('users').select('eclass_username').eq('id', user_id).execute()
                eclass_username = user_data_response.data[0]['eclass_username'] if user_data_response.data else None
                
                return {
                    "id": user_id,
                    "eclass_username": eclass_username,
                    "token": token
                }
            except Exception as table_error:
                logger.error(f"사용자 데이터 조회 실패: {str(table_error)}")
                # 테이블 조회 실패해도 기본 정보는 반환
                return {
                    "id": user_id,
                    "eclass_username": None,
                    "token": token
                }

        except HTTPException:
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
            # 토큰 유효성 확인
            try:
                user_response = self.supabase.auth.get_user(token)
                if not user_response or not user_response.user:
                    return {"status": "already_logged_out", "message": "이미 로그아웃된 상태입니다."}
            except Exception:
                return {"status": "already_logged_out", "message": "이미 로그아웃된 상태입니다."}

            # Supabase Auth 로그아웃
            try:
                self.supabase.auth.sign_out()
                logger.info("Supabase 로그아웃 성공")
            except Exception as logout_error:
                logger.warning(f"Supabase 로그아웃 중 오류 (무시): {str(logout_error)}")
                # Supabase 로그아웃 실패는 무시하고 성공으로 처리
                pass

            return {"status": "success", "message": "로그아웃되었습니다."}

        except Exception as e:
            logger.error(f"로그아웃 처리 중 오류: {str(e)}")
            raise Exception(f"로그아웃 처리 중 오류가 발생했습니다: {str(e)}")

    async def validate_eclass_credentials(self, eclass_id: str, eclass_pw: str) -> bool:
        """
        이클래스 계정 정보의 유효성 검증

        Args:
            eclass_id: 이클래스 아이디
            eclass_pw: 이클래스 비밀번호

        Returns:
            bool: 유효한 계정 정보인 경우 True, 아니면 False
        """
        try:
            # EclassSession 인스턴스 생성
            from app.services.session.eclass_session import EclassSession

            session = EclassSession()
            # 실제 로그인 시도
            login_success = await session.login(username=eclass_id, password=eclass_pw)

            # 세션 종료 (중요: 리소스 정리)
            await session.close()

            return login_success
        except Exception as e:
            logger.error(f"이클래스 계정 검증 중 오류: {str(e)}")
            return False


    async def get_user_eclass_credentials(self, user_id: str) -> Optional[Dict[str, str]]:
        """사용자의 이클래스 계정 정보 조회 (Supabase에서)"""
        try:
            # Supabase users 테이블에서 사용자 조회
            user_response = self.supabase.table('users').select('eclass_username, encrypted_session_token').eq('id', user_id).execute()
            
            if not user_response.data or len(user_response.data) == 0:
                logger.error(f"사용자 {user_id}를 찾을 수 없음")
                return None

            user_data = user_response.data[0]
            
            if not user_data.get('eclass_username') or not user_data.get('encrypted_session_token'):
                logger.error(f"사용자 {user_id}의 이클래스 계정 정보가 없음")
                return None

            # 비밀번호 복호화
            eclass_password = user_data['encrypted_session_token']
            if is_encrypted(eclass_password):
                try:
                    decrypted_password = decrypt_eclass_password(eclass_password)
                except Exception as decrypt_error:
                    logger.error(f"비밀번호 복호화 실패: {str(decrypt_error)}")
                    return None
            else:
                # 평문 비밀번호인 경우 (기존 데이터 호환성)
                decrypted_password = eclass_password
                logger.warning(f"평문 비밀번호 발견: 사용자 {user_id}")
            
            return {
                "username": user_data['eclass_username'],
                "password": decrypted_password
            }
        except Exception as e:
            logger.error(f"이클래스 계정 정보 조회 중 오류: {str(e)}")
            return None

    async def _update_eclass_password(self, user_id: str, eclass_password: str) -> None:
        """이클래스 비밀번호를 암호화하여 업데이트"""
        try:
            # 현재 저장된 비밀번호 확인
            user_response = self.supabase.table('users').select('encrypted_session_token').eq('id', user_id).execute()
            
            if user_response.data and len(user_response.data) > 0:
                stored_password = user_response.data[0].get('encrypted_session_token', '')
                
                # 이미 암호화된 상태이고 복호화했을 때 같은 비밀번호인 경우 스킵
                if is_encrypted(stored_password):
                    try:
                        decrypted_password = decrypt_eclass_password(stored_password)
                        if decrypted_password == eclass_password:
                            return  # 업데이트 불필요
                    except Exception:
                        pass  # 복호화 실패 시 새로 암호화하여 저장
                
                # 비밀번호 암호화하여 업데이트
                encrypted_password = encrypt_eclass_password(eclass_password)
                self.supabase.table('users').update({
                    'encrypted_session_token': encrypted_password
                }).eq('id', user_id).execute()
                
                logger.debug(f"사용자 {user_id}의 이클래스 비밀번호 업데이트 완료")
                
        except Exception as e:
            logger.error(f"이클래스 비밀번호 업데이트 중 오류: {str(e)}")
            # 비밀번호 업데이트 실패는 로그인 실패로 처리하지 않음

    async def sync_user_to_local_db(self, user_id: str, eclass_username: str, email: str = None) -> None:
        """
        Supabase에서 로컬 데이터베이스로 사용자 정보 동기화
        
        Args:
            user_id: Supabase 사용자 ID
            eclass_username: e-Class 사용자명
            email: 이메일 주소
        """
        try:
            async with AsyncSessionLocal() as db:
                # 기존 사용자 확인
                existing_user = await self.user_repository.get_by_id(db, user_id)
                
                if existing_user:
                    # 기존 사용자 정보 업데이트
                    await self.user_repository.update(
                        db, 
                        existing_user,
                        eclass_username=eclass_username,
                        email=email
                    )
                    logger.info(f"기존 사용자 정보 업데이트: {user_id}")
                else:
                    # 새 사용자 생성
                    await self.user_repository.create(
                        db,
                        id=user_id,
                        eclass_username=eclass_username,
                        email=email
                    )
                    logger.info(f"새 사용자 생성: {user_id}")
                    
        except Exception as e:
            logger.error(f"사용자 로컬 DB 동기화 중 오류: {str(e)}")
            # 동기화 실패는 인증 실패로 처리하지 않음