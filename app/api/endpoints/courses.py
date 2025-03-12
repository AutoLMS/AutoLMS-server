from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.course import Course, CourseList
from app.api.deps import get_current_user, get_db_session, get_eclass_service
from app.services.eclass_service import EclassService

router = APIRouter()

@router.get("/", response_model=CourseList)
async def get_courses(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    eclass_service: EclassService = Depends(get_eclass_service)
) -> Any:
    """모든 강의 목록 조회"""
    courses = await eclass_service.get_courses(current_user["id"], db)
    return {
        "courses": courses,
        "total": len(courses)
    }

@router.get("/{course_id}", response_model=Course)
async def get_course(
    course_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user),
    eclass_service: EclassService = Depends(get_eclass_service)
) -> Any:
    """특정 강의 정보 조회"""
    courses = await eclass_service.get_courses(current_user["id"], db)
    for course in courses:
        if course["id"] == course_id:
            return course
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="강의를 찾을 수 없습니다"
    )

@router.post("/refresh", response_model=CourseList)
async def refresh_courses(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user),
    eclass_service: EclassService = Depends(get_eclass_service)
) -> Any:
    """강의 목록 새로고침 (e-Class에서 다시 가져오기)"""
    # 강제 새로고침
    courses = await eclass_service.get_courses(current_user["id"], db, force_refresh=True)
    
    return {
        "courses": courses,
        "total": len(courses),
        "message": "강의 목록 새로고침이 완료되었습니다"
    }
