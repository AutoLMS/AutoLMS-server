import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from supabase import create_client

from app.core.config import settings
from app.utils.jwt_utils import jwt_manager

logger = logging.getLogger(__name__)

class SessionManager:
    """JWT와 eclass HTTP 세션을 통합 관리하는 세션 매니저"""
    
    def __init__(self):
        # Service key로 Supabase 클라이언트 초기화 (RLS 우회)
        self.supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    
    async def create_jwt_session(
        self,
        user_id: str,
        eclass_username: str,
        user_agent: str = None,
        ip_address: str = None
    ) -> Dict[str, Any]:
        """JWT 세션 생성"""
        try:
            # JWT 토큰 생성
            access_token = jwt_manager.create_access_token(user_id, eclass_username)
            refresh_token = jwt_manager.create_refresh_token(user_id)
            
            # 세션 만료 시간 (액세스 토큰 기준)
            expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
            
            # sessions 테이블에 저장
            session_data = {
                "user_id": user_id,
                "session_type": "jwt",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": expires_at.isoformat(),
                "user_agent": user_agent,
                "ip_address": ip_address,
                "is_active": True
            }
            
            result = self.supabase.table('sessions').insert(session_data).execute()
            
            if result.data:
                session_id = result.data[0]['id']
                logger.info(f"JWT 세션 생성 완료: user_id={user_id}, session_id={session_id}")
                
                return {
                    "session_id": session_id,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "expires_at": expires_at,
                    "session_type": "jwt"
                }
            else:
                raise Exception("세션 데이터 저장 실패")
                
        except Exception as e:
            logger.error(f"JWT 세션 생성 중 오류: {str(e)}")
            raise
    
    async def create_eclass_session(
        self,
        user_id: str,
        eclass_cookies: Dict[str, Any],
        eclass_session_id: str,
        user_agent: str = None,
        ip_address: str = None
    ) -> Dict[str, Any]:
        """eclass HTTP 세션 생성"""
        try:
            # eclass 세션은 보통 더 짧은 수명 (2시간)
            expires_at = datetime.now(timezone.utc) + timedelta(hours=2)
            
            session_data = {
                "user_id": user_id,
                "session_type": "eclass",
                "eclass_cookies": eclass_cookies,
                "eclass_session_id": eclass_session_id,
                "expires_at": expires_at.isoformat(),
                "user_agent": user_agent,
                "ip_address": ip_address,
                "is_active": True
            }
            
            result = self.supabase.table('sessions').insert(session_data).execute()
            
            if result.data:
                session_id = result.data[0]['id']
                logger.info(f"eclass 세션 생성 완료: user_id={user_id}, session_id={session_id}")
                
                return {
                    "session_id": session_id,
                    "eclass_cookies": eclass_cookies,
                    "eclass_session_id": eclass_session_id,
                    "expires_at": expires_at,
                    "session_type": "eclass"
                }
            else:
                raise Exception("eclass 세션 데이터 저장 실패")
                
        except Exception as e:
            logger.error(f"eclass 세션 생성 중 오류: {str(e)}")
            raise
    
    async def create_combined_session(
        self,
        user_id: str,
        eclass_username: str,
        eclass_cookies: Dict[str, Any],
        eclass_session_id: str,
        user_agent: str = None,
        ip_address: str = None
    ) -> Dict[str, Any]:
        """JWT + eclass 통합 세션 생성"""
        try:
            # JWT 토큰 생성
            access_token = jwt_manager.create_access_token(user_id, eclass_username)
            refresh_token = jwt_manager.create_refresh_token(user_id)
            
            # 만료 시간은 더 짧은 쪽 기준 (eclass 세션)
            expires_at = datetime.now(timezone.utc) + timedelta(hours=2)
            
            session_data = {
                "user_id": user_id,
                "session_type": "combined",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "eclass_cookies": eclass_cookies,
                "eclass_session_id": eclass_session_id,
                "expires_at": expires_at.isoformat(),
                "user_agent": user_agent,
                "ip_address": ip_address,
                "is_active": True
            }
            
            result = self.supabase.table('sessions').insert(session_data).execute()
            
            if result.data:
                session_id = result.data[0]['id']
                logger.info(f"통합 세션 생성 완료: user_id={user_id}, session_id={session_id}")
                
                return {
                    "session_id": session_id,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "eclass_cookies": eclass_cookies,
                    "eclass_session_id": eclass_session_id,
                    "expires_at": expires_at,
                    "session_type": "combined"
                }
            else:
                raise Exception("통합 세션 데이터 저장 실패")
                
        except Exception as e:
            logger.error(f"통합 세션 생성 중 오류: {str(e)}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 ID로 세션 조회"""
        try:
            result = self.supabase.table('sessions')\
                .select('*')\
                .eq('id', session_id)\
                .eq('is_active', True)\
                .single()\
                .execute()
            
            if result.data:
                return result.data
            return None
            
        except Exception as e:
            logger.error(f"세션 조회 중 오류: {str(e)}")
            return None
    
    async def get_user_sessions(self, user_id: str, session_type: str = None) -> List[Dict[str, Any]]:
        """사용자의 활성 세션 목록 조회"""
        try:
            query = self.supabase.table('sessions')\
                .select('*')\
                .eq('user_id', user_id)\
                .eq('is_active', True)\
                .order('created_at', desc=True)
            
            if session_type:
                query = query.eq('session_type', session_type)
            
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"사용자 세션 목록 조회 중 오류: {str(e)}")
            return []
    
    async def refresh_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 갱신 (JWT 토큰 갱신)"""
        try:
            session = await self.get_session(session_id)
            if not session or session.get('session_type') not in ['jwt', 'combined']:
                return None
            
            refresh_token = session.get('refresh_token')
            if not refresh_token:
                return None
            
            # 새 액세스 토큰 생성
            new_access_token = jwt_manager.refresh_access_token(refresh_token)
            new_expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
            
            # 세션 업데이트
            update_data = {
                "access_token": new_access_token,
                "expires_at": new_expires_at.isoformat(),
                "last_used": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            result = self.supabase.table('sessions')\
                .update(update_data)\
                .eq('id', session_id)\
                .execute()
            
            if result.data:
                logger.info(f"세션 갱신 완료: session_id={session_id}")
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"세션 갱신 중 오류: {str(e)}")
            return None
    
    async def invalidate_session(self, session_id: str) -> bool:
        """세션 무효화"""
        try:
            result = self.supabase.table('sessions')\
                .update({
                    "is_active": False,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                })\
                .eq('id', session_id)\
                .execute()
            
            success = bool(result.data)
            if success:
                logger.info(f"세션 무효화 완료: session_id={session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"세션 무효화 중 오류: {str(e)}")
            return False
    
    async def invalidate_user_sessions(self, user_id: str, exclude_session_id: str = None) -> int:
        """사용자의 모든 세션 무효화 (로그아웃 시 사용)"""
        try:
            query = self.supabase.table('sessions')\
                .update({
                    "is_active": False,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                })\
                .eq('user_id', user_id)\
                .eq('is_active', True)
            
            if exclude_session_id:
                query = query.neq('id', exclude_session_id)
            
            result = query.execute()
            
            count = len(result.data) if result.data else 0
            logger.info(f"사용자 세션 {count}개 무효화 완료: user_id={user_id}")
            
            return count
            
        except Exception as e:
            logger.error(f"사용자 세션 무효화 중 오류: {str(e)}")
            return 0
    
    async def cleanup_expired_sessions(self) -> int:
        """만료된 세션 정리 (백그라운드 작업)"""
        try:
            now = datetime.now(timezone.utc).isoformat()
            
            result = self.supabase.table('sessions')\
                .update({"is_active": False})\
                .lt('expires_at', now)\
                .eq('is_active', True)\
                .execute()
            
            count = len(result.data) if result.data else 0
            if count > 0:
                logger.info(f"만료된 세션 {count}개 정리 완료")
            
            return count
            
        except Exception as e:
            logger.error(f"만료된 세션 정리 중 오류: {str(e)}")
            return 0
    
    async def update_session_activity(self, session_id: str) -> bool:
        """세션 활동 시간 업데이트"""
        try:
            result = self.supabase.table('sessions')\
                .update({
                    "last_used": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                })\
                .eq('id', session_id)\
                .eq('is_active', True)\
                .execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"세션 활동 시간 업데이트 중 오류: {str(e)}")
            return False

# 싱글톤 인스턴스
session_manager = SessionManager()