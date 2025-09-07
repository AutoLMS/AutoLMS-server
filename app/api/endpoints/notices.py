from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.notice import Notice, NoticeList
from app.api.deps import get_current_user, get_db_session, get_eclass_service
from app.services.eclass_service import EclassService
from app.services.test_data_service import TestDataService
from app.core.config import settings

router = APIRouter()

def get_test_data_service():
    return TestDataService()

@router.get("/", response_model=NoticeList)
async def get_notices(
    course_id: str = Path(..., description="강의 ID"),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user),
    eclass_service: EclassService = Depends(get_eclass_service),
    test_data_service: TestDataService = Depends(get_test_data_service)
) -> Any:
    """강의 공지사항 목록 조회"""
    
    # 개발 환경에서는 테스트 데이터 사용
    if settings.ENVIRONMENT == "development":
        notices = test_data_service.get_notices(current_user["id"], course_id)
        return {
            "notices": notices,
            "total": len(notices)
        }
    
    notices = await eclass_service.get_notices(current_user["id"], course_id, is_jwt_user=True)
    return {
        "notices": notices,
        "total": len(notices)
    }

@router.get("/{notice_id}", response_model=Notice)
async def get_notice(
    course_id: str = Path(..., description="강의 ID"),
    notice_id: str = Path(..., description="공지사항 ID"),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user),
    eclass_service: EclassService = Depends(get_eclass_service),
    test_data_service: TestDataService = Depends(get_test_data_service)
) -> Any:
    """특정 공지사항 조회"""
    
    # 개발 환경에서는 테스트 데이터 사용
    if settings.ENVIRONMENT == "development":
        notices = test_data_service.get_notices(current_user["id"], course_id)
        for notice in notices:
            if notice["article_id"] == notice_id:
                return notice
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="공지사항을 찾을 수 없습니다"
        )
    
    notices = await eclass_service.get_notices(current_user["id"], course_id, is_jwt_user=True)
    for notice in notices:
        if notice["article_id"] == notice_id:
            return notice
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="공지사항을 찾을 수 없습니다"
    )

@router.post("/refresh")
async def refresh_notices(
    course_id: str = Path(..., description="강의 ID"),
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user),
    eclass_service: EclassService = Depends(get_eclass_service),
    test_data_service: TestDataService = Depends(get_test_data_service)
) -> Any:
    """공지사항 새로고침"""
    
    # 개발 환경에서는 테스트 데이터 사용
    if settings.ENVIRONMENT == "development":
        notices = test_data_service.get_notices(current_user["id"], course_id)
        return {
            "notices": notices,
            "total": len(notices),
            "message": "공지사항 새로고침이 완료되었습니다"
        }
    
    result = await eclass_service.crawl_course(current_user["id"], course_id, is_jwt_user=True)
    
    # 새로운 공지사항 조회
    notices = await eclass_service.get_notices(current_user["id"], course_id, is_jwt_user=True)
    
    return {
        "notices": notices,
        "total": len(notices),
        "message": "공지사항 새로고침이 완료되었습니다",
        "crawl_result": result
    }
