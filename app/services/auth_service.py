import logging

from fastapi import HTTPException, status
from typing import Dict, Any, Optional
from sqlalchemy import select
from app.models.user import User
from supabase.lib.client_options import ClientOptions
from postgrest.exceptions import APIError
import traceback
from datetime import datetime

from app.core.config import settings
from app.core.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

class AuthService:
    """Supabase Auth 기반 인증 서비스"""

    def __init__(self, supabase_client=None):
        self.supabase = supabase_client or get_supabase_client()

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

            # 자동으로 이메일과 패스워드 생성
            auto_email = f"seoultech@{eclass_username}"
            import uuid
            auto_password = str(uuid.uuid4())  # 랜덤 패스워드 생성
            
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

                    # 저장할 사용자 데이터 구성
                    user_data = {
                        'id': user_id,
                        'eclass_username': eclass_username,
                        'eclass_password': eclass_password,  # 실제 구현에서는 암호화 필요
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

                return {
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

            # 자동 생성된 이메일로 Supabase 사용자 조회
            auto_email = f"seoultech@{eclass_username}"
            
            # 사용자 정보 조회
            try:
                user_response = self.supabase.table('users').select('*').eq('eclass_username', eclass_username).execute()
                
                if not user_response.data or len(user_response.data) == 0:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="등록되지 않은 이클래스 계정입니다. 먼저 회원가입을 진행해주세요."
                    )
                
                user_data = user_response.data[0]
                user_id = user_data['id']
                
                # 임시 토큰 생성 (실제로는 JWT 토큰 생성)
                import uuid
                access_token = str(uuid.uuid4())
                
                return {
                    "session": {
                        "access_token": access_token,
                        "refresh_token": str(uuid.uuid4())
                    },
                    "user": {
                        "id": user_id,
                        "eclass_username": eclass_username
                    }
                }
                
            except Exception as db_error:
                logger.error(f"사용자 정보 조회 중 오류: {str(db_error)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="로그인 처리 중 오류가 발생했습니다."
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

            # 사용자 정보 조회 시도
            try:
                user_response = self.supabase.auth.get_user(token)
                logger.info(f"User response received: {user_response}")

                if not user_response or not user_response.user:
                    logger.error("No user data in response")
                    raise ValueError("사용자 정보를 찾을 수 없습니다.")

                # 사용자 정보 반환 (이클래스 유저명 포함)
                user_data_response = self.supabase.table('users').select('eclass_username').eq('id', user_response.user.id).execute()
                eclass_username = user_data_response.data[0]['eclass_username'] if user_data_response.data else None
                
                return {
                    "id": user_response.user.id,
                    "eclass_username": eclass_username,
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
        """사용자의 이클래스 계정 정보 조회"""
        try:
            from app.db.base import AsyncSessionLocal

            async with AsyncSessionLocal() as db:
                # ORM 방식으로 사용자 조회
                query = select(User).where(User.id == user_id)
                result = await db.execute(query)
                user = result.scalar_one_or_none()

                if not user:
                    logger.error(f"사용자 {user_id}를 찾을 수 없음")
                    return None

                if not user.eclass_username or not user.eclass_password:
                    logger.error(f"사용자 {user_id}의 이클래스 계정 정보가 없음")
                    return None

                return {
                    "username": user.eclass_username,
                    "password": user.eclass_password
                }
        except Exception as e:
            logger.error(f"이클래스 계정 정보 조회 중 오류: {str(e)}")
            return None