import jwt
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)

class JWTManager:
    """자체 JWT 토큰 관리 시스템"""
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_hours = 24  # 24시간
        self.refresh_token_expire_days = 30   # 30일
    
    def create_access_token(self, user_id: str, eclass_username: str) -> str:
        """액세스 토큰 생성"""
        try:
            expire = datetime.now(timezone.utc) + timedelta(hours=self.access_token_expire_hours)
            payload = {
                "user_id": user_id,
                "eclass_username": eclass_username,
                "token_type": "access",
                "exp": expire,
                "iat": datetime.now(timezone.utc),
                "sub": user_id  # JWT standard claim
            }
            
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            logger.debug(f"액세스 토큰 생성 완료: user_id={user_id}")
            return token
            
        except Exception as e:
            logger.error(f"액세스 토큰 생성 중 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="토큰 생성에 실패했습니다."
            )
    
    def create_refresh_token(self, user_id: str) -> str:
        """리프레시 토큰 생성"""
        try:
            expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)
            payload = {
                "user_id": user_id,
                "token_type": "refresh",
                "exp": expire,
                "iat": datetime.now(timezone.utc),
                "sub": user_id
            }
            
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            logger.debug(f"리프레시 토큰 생성 완료: user_id={user_id}")
            return token
            
        except Exception as e:
            logger.error(f"리프레시 토큰 생성 중 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="리프레시 토큰 생성에 실패했습니다."
            )
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """토큰 검증 및 페이로드 반환"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # 토큰 타입 확인
            if payload.get("token_type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"잘못된 토큰 타입입니다. 예상: {token_type}"
                )
            
            # 만료 확인
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp, timezone.utc) < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="토큰이 만료되었습니다."
                )
            
            logger.debug(f"토큰 검증 성공: user_id={payload.get('user_id')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("만료된 토큰 접근 시도")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="토큰이 만료되었습니다."
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"유효하지 않은 토큰: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 토큰입니다."
            )
        except Exception as e:
            logger.error(f"토큰 검증 중 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="토큰 검증에 실패했습니다."
            )
    
    def refresh_access_token(self, refresh_token: str) -> str:
        """리프레시 토큰으로 새 액세스 토큰 생성"""
        try:
            # 리프레시 토큰 검증
            payload = self.verify_token(refresh_token, "refresh")
            user_id = payload.get("user_id")
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="유효하지 않은 리프레시 토큰입니다."
                )
            
            # TODO: 데이터베이스에서 사용자 정보 조회하여 eclass_username 가져오기
            # 임시로 payload에서 가져오거나 별도 조회 필요
            eclass_username = payload.get("eclass_username", "")
            
            # 새 액세스 토큰 생성
            new_access_token = self.create_access_token(user_id, eclass_username)
            
            logger.info(f"액세스 토큰 갱신 완료: user_id={user_id}")
            return new_access_token
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"토큰 갱신 중 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="토큰 갱신에 실패했습니다."
            )
    
    def decode_token_unsafe(self, token: str) -> Optional[Dict[str, Any]]:
        """토큰을 검증 없이 디코딩 (디버깅용)"""
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except Exception as e:
            logger.error(f"토큰 디코딩 오류: {str(e)}")
            return None
    
    def get_token_expiry(self, token: str) -> Optional[datetime]:
        """토큰 만료 시간 조회"""
        try:
            payload = self.decode_token_unsafe(token)
            if payload and "exp" in payload:
                return datetime.fromtimestamp(payload["exp"], timezone.utc)
            return None
        except Exception as e:
            logger.error(f"토큰 만료 시간 조회 오류: {str(e)}")
            return None

# 싱글톤 인스턴스
jwt_manager = JWTManager()