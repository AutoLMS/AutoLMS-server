from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import Any

from app.schemas.auth import EClassAuthRequest, EClassToken
from app.services.auth_service import AuthService
from app.api.deps import get_auth_service

router = APIRouter()

bearer_scheme = HTTPBearer()

@router.post("/register", response_model=EClassToken)
async def register(
    auth_request: EClassAuthRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> Any:
    """eClass 계정으로 회원가입"""
    result = await auth_service.eclass_register(
        eclass_username=auth_request.eclass_username,
        eclass_password=auth_request.eclass_password
    )
    return result

@router.post("/login", response_model=EClassToken)
async def login(
    auth_request: EClassAuthRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> Any:
    """eClass 계정으로 로그인"""
    result = await auth_service.eclass_login(
        eclass_username=auth_request.eclass_username,
        eclass_password=auth_request.eclass_password
    )
    return result

@router.get("/me")
async def get_current_user_info(
    token: str = Depends(bearer_scheme),
    auth_service: AuthService = Depends(get_auth_service)
) -> Any:
    """현재 사용자 정보 조회"""
    # HTTPBearer에서는 token.credentials로 실제 토큰 값을 가져옴
    actual_token = token.credentials if hasattr(token, 'credentials') else str(token)
    current_user = await auth_service.get_current_user(actual_token)
    return current_user

@router.post("/logout")
async def logout(
    token: str = Depends(bearer_scheme),
    auth_service: AuthService = Depends(get_auth_service)
) -> Any:
    """로그아웃"""
    try:
        actual_token = token.credentials if hasattr(token, 'credentials') else str(token)
        result = await auth_service.logout(actual_token)

        # 이미 로그아웃된 상태 처리
        if result.get("status") == "already_logged_out":
            return {"message": result.get("message"), "status": "already_logged_out"}

        return {"message": "로그아웃 성공", "status": "success"}
    except Exception as e:
        # 오류 발생 시 처리
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )