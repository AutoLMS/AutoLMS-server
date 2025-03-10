from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.supabase_client import get_supabase_client

class AuthService:
    """Supabase Auth 기반 인증 서비스"""
    
    def __init__(self, supabase_client=None):
        self.supabase = supabase_client or get_supabase_client()
    
    async def register(self, email: str, password: str) -> Dict[str, Any]:
        """새 사용자 등록"""
        # TODO: 회원가입 구현
        return {"message": "Not implemented"}
    
    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """사용자 로그인"""
        # TODO: 로그인 구현
        return {"message": "Not implemented"}
    
    async def get_current_user(self, token: str) -> Dict[str, Any]:
        """토큰에서 현재 사용자 정보 추출"""
        # TODO: 토큰 검증 구현
        return {"id": "mock_user_id", "email": "mock@example.com"}
    
    async def logout(self, token: str) -> Dict[str, Any]:
        """사용자 로그아웃"""
        # TODO: 로그아웃 구현
        return {"message": "Not implemented"}
