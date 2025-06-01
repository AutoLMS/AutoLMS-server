from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session, get_eclass_service
from app.services.eclass_service import EclassService

router = APIRouter()

@router.post("/all")
async def crawl_all_courses(
    auto_download: Optional[bool] = False,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user),
    eclass_service: EclassService = Depends(get_eclass_service)
) -> Any:
    """모든 강의 자동 크롤링 시작"""
    result = await eclass_service.crawl_all_courses(
        user_id=current_user["id"],
        auto_download=auto_download
    )

    return result

@router.post("/course/{course_id}")
async def crawl_specific_course(
    course_id: str,
    auto_download: Optional[bool] = False,
    current_user: dict = Depends(get_current_user),
    eclass_service: EclassService = Depends(get_eclass_service)
) -> Any:
    """특정 강의 자동 크롤링 시작"""
    result = await eclass_service.crawl_course(
        user_id=current_user["id"],
        course_id=course_id,
        auto_download=auto_download
    )

    return result

@router.get("/status/{task_id}")
async def get_crawling_status(
    task_id: str,
    current_user: dict = Depends(get_current_user),
    eclass_service: EclassService = Depends(get_eclass_service)
) -> Any:
    """크롤링 작업 상태 조회"""
    task_status = await eclass_service.get_task_status(task_id)

    if task_status.get("status") == "not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"작업 ID {task_id}를 찾을 수 없습니다"
        )

    return task_status

@router.post("/cancel/{task_id}")
async def cancel_crawling_task(
    task_id: str,
    current_user: dict = Depends(get_current_user),
    eclass_service: EclassService = Depends(get_eclass_service)
) -> Any:
    """크롤링 작업 취소"""
    cancelled = await eclass_service.cancel_task(task_id)

    if not cancelled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"작업 ID {task_id}를 찾을 수 없거나 이미 완료된 작업입니다"
        )

    return {
        "status": "success",
        "message": f"작업 ID {task_id}가 취소되었습니다"
    }
