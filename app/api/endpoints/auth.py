from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Any

from app.schemas.auth import UserCreate, Token, UserOut
from app.services.auth_service import AuthService
from app.api.deps import get_auth_service

router = APIRouter()

@router.post("/register", response_model=UserOut)
async def register(
    user_in: UserCreate,
    auth_service: AuthService = Depends(get_auth_service)
) -> Any:
    """새 사용자 등록"""
    result = await auth_service.register(email=user_in.email, password=user_in.password)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="회원가입 중 오류가 발생했습니다."
        )
    
    return result.get("user", {})

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
) -> Any:
    """로그인 및 토큰 발급"""
    result = await auth_service.login(email=form_data.username, password=form_data.password)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {
        "access_token": result.get("session", {}).get("access_token", ""),
        "token_type": "bearer",
        "user": result.get("user", {})
    }

@router.post("/logout")
async def logout(
    auth_service: AuthService = Depends(get_auth_service),
    token: str = Depends(get_auth_service)
) -> Any:
    """로그아웃"""
    await auth_service.logout(token)
    return {"message": "로그아웃 성공"}
