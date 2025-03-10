from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.db.session import get_db
from app.services.auth_service import AuthService
from app.core.supabase_client import get_supabase_client

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def get_auth_service() -> AuthService:
    """인증 서비스 제공"""
    return AuthService(get_supabase_client())

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service)
):
    """현재 로그인한 사용자 확인"""
    return await auth_service.get_current_user(token)
