import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any, Dict

from app.api.deps import get_current_user
from app.services.scheduler_service import scheduler_service
from app.services.auto_refresh_service import auto_refresh_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/status")
async def get_scheduler_status(
    current_user: dict = Depends(get_current_user)
) -> Any:
    """스케줄러 상태 조회"""
    try:
        status = scheduler_service.get_task_status()
        return {
            "scheduler": status,
            "timestamp": status.get("timestamp"),
            "user_id": current_user.get("id")
        }
    except Exception as e:
        logger.error(f"스케줄러 상태 조회 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="스케줄러 상태 조회 중 오류가 발생했습니다."
        )

@router.get("/auto-refresh/status")
async def get_auto_refresh_status(
    current_user: dict = Depends(get_current_user)
) -> Any:
    """자동 새로고침 상태 조회"""
    try:
        user_id = current_user.get("id")
        status = await auto_refresh_service.get_refresh_status(user_id)
        return status
    except Exception as e:
        logger.error(f"자동 새로고침 상태 조회 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="자동 새로고침 상태 조회 중 오류가 발생했습니다."
        )

@router.post("/auto-refresh/trigger")
async def trigger_auto_refresh(
    force: bool = False,
    current_user: dict = Depends(get_current_user)
) -> Any:
    """수동으로 자동 새로고침 실행"""
    try:
        user_id = current_user.get("id")
        result = await auto_refresh_service.refresh_user_content(user_id, force=force)
        
        return {
            "success": True,
            "message": "자동 새로고침이 완료되었습니다.",
            "result": result
        }
    except Exception as e:
        logger.error(f"수동 자동 새로고침 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"자동 새로고침 실행 중 오류가 발생했습니다: {str(e)}"
        )

@router.put("/auto-refresh/config/{course_id}")
async def update_auto_refresh_config(
    course_id: str,
    config_updates: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
) -> Any:
    """자동 새로고침 설정 업데이트"""
    try:
        user_id = current_user.get("id")
        
        success = await auto_refresh_service.update_config(
            user_id=user_id,
            course_id=course_id,
            **config_updates
        )
        
        if success:
            return {
                "success": True,
                "message": "자동 새로고침 설정이 업데이트되었습니다.",
                "user_id": user_id,
                "course_id": course_id
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 강의의 자동 새로고침 설정을 찾을 수 없습니다."
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"자동 새로고침 설정 업데이트 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="자동 새로고침 설정 업데이트 중 오류가 발생했습니다."
        )

@router.post("/auto-refresh/config/{course_id}")
async def add_auto_refresh_config(
    course_id: str,
    config: Dict[str, Any] = {},
    current_user: dict = Depends(get_current_user)
) -> Any:
    """자동 새로고침 설정 추가"""
    try:
        user_id = current_user.get("id")
        
        await auto_refresh_service.add_auto_refresh_config(
            user_id=user_id,
            course_id=course_id,
            **config
        )
        
        return {
            "success": True,
            "message": "자동 새로고침 설정이 추가되었습니다.",
            "user_id": user_id,
            "course_id": course_id
        }
    except Exception as e:
        logger.error(f"자동 새로고침 설정 추가 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="자동 새로고침 설정 추가 중 오류가 발생했습니다."
        )

@router.delete("/auto-refresh/config/{course_id}")
async def remove_auto_refresh_config(
    course_id: str,
    current_user: dict = Depends(get_current_user)
) -> Any:
    """자동 새로고침 설정 제거"""
    try:
        user_id = current_user.get("id")
        
        await auto_refresh_service.remove_auto_refresh_config(
            user_id=user_id,
            course_id=course_id
        )
        
        return {
            "success": True,
            "message": "자동 새로고침 설정이 제거되었습니다.",
            "user_id": user_id,
            "course_id": course_id
        }
    except Exception as e:
        logger.error(f"자동 새로고침 설정 제거 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="자동 새로고침 설정 제거 중 오류가 발생했습니다."
        )