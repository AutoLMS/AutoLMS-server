from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from app.api.deps import get_current_user, get_db_session, get_eclass_service
from app.services.eclass_service import EclassService
from app.services.test_data_service import TestDataService
from app.core.config import settings

router = APIRouter()

def get_test_data_service():
    return TestDataService()

@router.get("", response_model=Dict[str, Any])
async def get_syllabus(
    course_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    eclass_service: EclassService = Depends(get_eclass_service),
    test_data_service: TestDataService = Depends(get_test_data_service)
) -> Dict[str, Any]:
    """강의계획서 조회"""
    
    # 개발 환경에서는 테스트 데이터 사용
    if settings.ENVIRONMENT == "development":
        course = test_data_service.get_course_by_id(current_user["id"], course_id)
        if not course:
            raise HTTPException(status_code=404, detail="강의를 찾을 수 없습니다")
        
        # 간단한 강의계획서 정보 반환
        return {
            "course_id": course_id,
            "course_name": course["name"],
            "course_code": course["code"],
            "course_time": course["time"],
            "syllabus_available": True,
            "message": "강의계획서 정보 (테스트 데이터)"
        }
    
    try:
        syllabus = await eclass_service.get_syllabus(current_user["id"], course_id, db)
        return syllabus
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
