from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any

from app.schemas.course import Course, CourseList
from app.api.deps import (
    get_current_user,
    get_course_service,
    get_notice_service,
    get_material_service,
    get_assignment_service,
    get_syllabus_service
)
from app.services.content.course_service import CourseService
from app.services.content.notice_service import NoticeService
from app.services.content.material_service import MaterialService
from app.services.content.assignment_service import AssignmentService
from app.services.content.syllabus_service import SyllabusService

router = APIRouter()

@router.get("/", response_model=CourseList)
async def get_courses(
    current_user: dict = Depends(get_current_user),
    course_service: CourseService = Depends(get_course_service)
) -> Any:
    """
    사용자의 모든 강의 목록 조회 (스마트 자동 크롤링 포함)
    
    - 기존에 저장된 강의 목록을 우선적으로 반환
    - 신규 사용자이거나 강의 목록이 비어있는 경우 자동으로 이클래스에서 크롤링
    - 빠른 응답을 위해 캐시된 데이터를 활용
    """
    courses = await course_service.get_courses(user_id=current_user["id"])
    return {
        "courses": courses,
        "total": len(courses)
    }

@router.get("/refresh", response_model=CourseList)
async def refresh_courses(
    current_user: dict = Depends(get_current_user),
    course_service: CourseService = Depends(get_course_service)
) -> Any:
    """
    이클래스에서 최신 강의 목록을 가져와 데이터베이스 동기화
    
    - 이클래스 웹사이트에서 실시간으로 강의 목록을 크롤링
    - 새로운 강의는 추가하고 기존 강의는 업데이트
    - 신규 사용자의 경우 최초 강의 목록 수집에 사용
    """
    courses = await course_service.refresh_courses(user_id=current_user["id"])
    return {
        "courses": courses,
        "total": len(courses),
        "message": "강의 목록이 새로고침되었습니다."
    }

@router.get("/sync", response_model=dict)
async def sync_course(
    course_id: str,
    current_user: dict = Depends(get_current_user),
    course_service: CourseService = Depends(get_course_service),
    notice_service: NoticeService = Depends(get_notice_service),
    material_service: MaterialService = Depends(get_material_service),
    assignment_service: AssignmentService = Depends(get_assignment_service),
    syllabus_service: SyllabusService = Depends(get_syllabus_service)
) -> Any:
    """특정 강의 전체 동기화"""
    # 1. 강의 정보 새로고침
    course = await course_service.get_course(current_user["id"], course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="강의를 찾을 수 없습니다."
        )

    # 2. 각 콘텐츠 타입별 동기화
    result = {
        "course_id": course_id,
        "course_name": course.name,
        "notices": await notice_service.refresh_all(course_id, current_user["id"], auto_download=True),
        "materials": await material_service.refresh_all(course_id, current_user["id"], auto_download=True),
        "assignments": await assignment_service.refresh_all(course_id, current_user["id"], auto_download=True),
        "syllabus": await syllabus_service.refresh_all(course_id, current_user["id"]),
    }

    return result

@router.get("/{course_id}", response_model=Course)
async def get_course(
    course_id: str,
    current_user: dict = Depends(get_current_user),
    course_service: CourseService = Depends(get_course_service)
) -> Any:
    """특정 강의 조회"""
    course = await course_service.get_course(current_user["id"], course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="강의를 찾을 수 없습니다."
        )
    return course
