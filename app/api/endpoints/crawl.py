from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_current_user,
    get_db_session,
    get_session_service,
    get_course_service,
    get_notice_service,
    get_material_service,
    get_assignment_service,
    get_syllabus_service
)
from app.services.core.session_service import SessionService
from app.services.content.course_service import CourseService
from app.services.content.notice_service import NoticeService
from app.services.content.material_service import MaterialService
from app.services.content.assignment_service import AssignmentService
from app.services.content.syllabus_service import SyllabusService

router = APIRouter()


@router.post("/sync/course/{course_id}")
async def sync_course(
        course_id: str,
        auto_download: bool = True,
        db: AsyncSession = Depends(get_db_session),
        current_user: dict = Depends(get_current_user),
        course_service: CourseService = Depends(get_course_service),
        notice_service: NoticeService = Depends(get_notice_service),
        material_service: MaterialService = Depends(get_material_service),
        assignment_service: AssignmentService = Depends(get_assignment_service),
        syllabus_service: SyllabusService = Depends(get_syllabus_service)
) -> Dict[str, Any]:
    """특정 강의 전체 동기화"""
    try:
        # 강의 존재 확인
        course = await course_service.get_course(current_user["id"], course_id, db)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="강의를 찾을 수 없습니다."
            )

        # 각 콘텐츠 타입별 동기화 실행
        result = {
            "course_id": course_id,
            "course_name": course.name,
            "status": "success",
            "details": {
                "notices": await notice_service.refresh_all(db, course_id, current_user["id"], auto_download),
                "materials": await material_service.refresh_all(db, course_id, current_user["id"], auto_download),
                "assignments": await assignment_service.refresh_all(db, course_id, current_user["id"], auto_download),
                "syllabus": bool(await syllabus_service.refresh(db, course_id, current_user["id"]))
            }
        }

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"동기화 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/sync/all")
async def sync_all_courses(
        background_tasks: BackgroundTasks,
        auto_download: bool = True,
        db: AsyncSession = Depends(get_db_session),
        current_user: dict = Depends(get_current_user),
        session_service: SessionService = Depends(get_session_service),
        course_service: CourseService = Depends(get_course_service),
        notice_service: NoticeService = Depends(get_notice_service),
        material_service: MaterialService = Depends(get_material_service),
        assignment_service: AssignmentService = Depends(get_assignment_service),
        syllabus_service: SyllabusService = Depends(get_syllabus_service)
) -> Dict[str, Any]:
    """모든 강의 동기화"""
    try:
        # 강의 목록 새로고침
        courses = await course_service.get_courses(current_user["id"], db, force_refresh=True)

        if not courses:
            return {
                "status": "error",
                "message": "동기화할 강의가 없습니다.",
                "courses": []
            }

        # 각 강의별 동기화 작업 준비
        async def sync_course_background(course_id: str) -> Dict[str, Any]:
            return await sync_course(
                course_id=course_id,
                auto_download=auto_download,
                db=db,
                current_user=current_user,
                course_service=course_service,
                notice_service=notice_service,
                material_service=material_service,
                assignment_service=assignment_service,
                syllabus_service=syllabus_service
            )

        # 백그라운드 작업으로 동기화 실행
        for course in courses:
            background_tasks.add_task(sync_course_background, course.id)

        return {
            "status": "started",
            "message": f"모든 강의 동기화가 시작되었습니다 ({len(courses)}개)",
            "courses": [{"id": course.id, "name": course.name} for course in courses]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"동기화 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/status/{task_id}")
async def get_sync_status(
        task_id: str,
        current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """동기화 작업 상태 확인"""
    # task_id에 해당하는 작업 상태 반환
    # 이 부분은 작업 추적 시스템에 따라 구현 필요
    return {
        "task_id": task_id,
        "status": "not_implemented",
        "message": "작업 상태 추적 기능이 구현되지 않았습니다."
    }


@router.post("/cancel/{task_id}")
async def cancel_sync(
        task_id: str,
        current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """동기화 작업 취소"""
    # task_id에 해당하는 작업 취소
    # 이 부분은 작업 추적 시스템에 따라 구현 필요
    return {
        "task_id": task_id,
        "status": "not_implemented",
        "message": "작업 취소 기능이 구현되지 않았습니다."
    }