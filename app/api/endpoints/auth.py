from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Any

from app.schemas.auth import Token, UserOut
from app.api.deps import (
    get_auth_service,
    get_session_service,
    oauth2_scheme
)
from app.services.auth_service import AuthService
from app.services.core.session_service import SessionService

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        auth_service: AuthService = Depends(get_auth_service),
        session_service: SessionService = Depends(get_session_service)
) -> Any:
    """로그인 및 토큰 발급"""
    try:
        # eclass 로그인 검증
        eclass_session = await session_service.get_session(
            eclass_id=form_data.username,
            password=form_data.password
        )

        if not eclass_session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="잘못된 학번 또는 비밀번호입니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # AutoLMS 서비스 로그인 (Supabase Auth)
        auth_result = await auth_service.login(
            email=form_data.username,
            password=form_data.password
        )

        if not auth_result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="서비스 로그인에 실패했습니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return {
            "access_token": auth_result["session"]["access_token"],
            "token_type": "bearer",
            "user": auth_result["user"]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"로그인 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/register", response_model=UserOut)
async def register(
        form_data: OAuth2PasswordRequestForm = Depends(),
        auth_service: AuthService = Depends(get_auth_service),
        session_service: SessionService = Depends(get_session_service)
) -> Any:
    """회원가입"""
    try:
        # eclass 로그인 검증
        eclass_session = await session_service.get_session(
            eclass_id=form_data.username,
            password=form_data.password
        )

        if not eclass_session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="잘못된 학번 또는 비밀번호입니다."
            )

        # AutoLMS 서비스 회원가입
        result = await auth_service.register(
            email=form_data.username,
            password=form_data.password
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="회원가입 중 오류가 발생했습니다."
            )

        return result.get("user", {})

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"회원가입 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/logout")
async def logout(
        token: str = Depends(oauth2_scheme),
        auth_service: AuthService = Depends(get_auth_service),
        session_service: SessionService = Depends(get_session_service)
) -> Any:
    """로그아웃"""
    try:
        # AutoLMS 서비스 로그아웃
        await auth_service.logout(token)

        # e-Class 세션 종료
        await session_service.end_session(token)

        return {
            "message": "로그아웃 성공",
            "status": "success"
        }

    except ValueError as e:
        return {
            "message": str(e),
            "status": "already_logged_out"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"로그아웃 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/verify", response_model=UserOut)
async def verify_token(
        token: str = Depends(oauth2_scheme),
        session_service: SessionService = Depends(get_session_service)
) -> Any:
    """토큰 검증"""
    try:
        user = await session_service.verify_token(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 토큰입니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )