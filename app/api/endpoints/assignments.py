from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.assignment import Assignment, AssignmentList
from app.api.deps import get_current_user, get_db_session, get_eclass_service
from app.services.eclass_service import EclassService
from app.services.test_data_service import TestDataService
from app.core.config import settings

router = APIRouter()

def get_test_data_service():
    return TestDataService()

@router.get("/", response_model=AssignmentList)
async def get_assignments(
    course_id: str = Path(..., description="강의 ID"),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user),
    eclass_service: EclassService = Depends(get_eclass_service),
    test_data_service: TestDataService = Depends(get_test_data_service)
) -> Any:
    """과제 목록 조회"""
    
    # 개발 환경에서는 테스트 데이터 사용
    if settings.ENVIRONMENT == "development":
        assignments = test_data_service.get_assignments(current_user["id"], course_id)
        return {
            "assignments": assignments,
            "total": len(assignments)
        }
    
    assignments = await eclass_service.get_assignments(current_user["id"], course_id, is_jwt_user=True)
    return {
        "assignments": assignments,
        "total": len(assignments)
    }

@router.get("/{assignment_id}", response_model=Assignment)
async def get_assignment(
    course_id: str = Path(..., description="강의 ID"),
    assignment_id: str = Path(..., description="과제 ID"),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user),
    eclass_service: EclassService = Depends(get_eclass_service),
    test_data_service: TestDataService = Depends(get_test_data_service)
) -> Any:
    """특정 과제 조회"""
    
    # 개발 환경에서는 테스트 데이터 사용
    if settings.ENVIRONMENT == "development":
        assignments = test_data_service.get_assignments(current_user["id"], course_id)
        for assignment in assignments:
            if assignment["assignment_id"] == assignment_id:
                return assignment
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="과제를 찾을 수 없습니다"
        )
    
    assignments = await eclass_service.get_assignments(current_user["id"], course_id, is_jwt_user=True)
    for assignment in assignments:
        if assignment["assignment_id"] == assignment_id:
            return assignment
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="과제를 찾을 수 없습니다"
    )

@router.post("/refresh")
async def refresh_assignments(
    course_id: str = Path(..., description="강의 ID"),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user),
    eclass_service: EclassService = Depends(get_eclass_service),
    test_data_service: TestDataService = Depends(get_test_data_service)
) -> Any:
    """과제 새로고침"""
    
    # 개발 환경에서는 테스트 데이터 사용
    if settings.ENVIRONMENT == "development":
        assignments = test_data_service.get_assignments(current_user["id"], course_id)
        return {
            "assignments": assignments,
            "total": len(assignments),
            "message": "과제 새로고침이 완료되었습니다"
        }
    
    result = await eclass_service.crawl_course(current_user["id"], course_id, is_jwt_user=True)
    
    # 새로운 과제 조회
    assignments = await eclass_service.get_assignments(current_user["id"], course_id, is_jwt_user=True)
    
    return {
        "assignments": assignments,
        "total": len(assignments),
        "message": "과제 새로고침이 완료되었습니다",
        "crawl_result": result
    }
