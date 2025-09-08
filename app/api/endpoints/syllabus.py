from fastapi import APIRouter, Depends, HTTPException, Path
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
    course_id: str = Path(..., description="강의 ID"),
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
    
    # 프로덕션 환경에서는 eClass 로그인 확인
    if not await eclass_service.is_logged_in():
        try:
            # AuthService를 통해 eClass 로그인 정보 가져오기
            from app.services.auth_service import AuthService
            auth_service = AuthService()
            eclass_credentials = await auth_service.get_user_eclass_credentials(current_user["id"])
            
            login_success = await eclass_service.login(
                eclass_credentials["eclass_username"], 
                eclass_credentials["eclass_password"]
            )
            if not login_success:
                raise HTTPException(
                    status_code=401,
                    detail="e-Class 로그인에 실패했습니다."
                )
        except Exception as e:
            raise HTTPException(
                status_code=401,
                detail=f"e-Class 로그인 중 오류가 발생했습니다: {str(e)}"
            )
    
    try:
        syllabus = await eclass_service.get_syllabus(current_user["id"], course_id)
        return syllabus
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
