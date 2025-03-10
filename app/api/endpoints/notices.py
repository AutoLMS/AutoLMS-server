from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any
from sqlalchemy.orm import Session

from app.schemas.notice import Notice, NoticeList
from app.api.deps import get_current_user, get_db
from app.services.eclass_service import EclassService

router = APIRouter()

@router.get("/", response_model=NoticeList)
async def get_notices(
    course_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    eclass_service: EclassService = Depends(lambda: EclassService())
) -> Any:
    """강의 공지사항 목록 조회"""
    notices = await eclass_service.get_notices(current_user["id"], course_id, db)
    return {
        "notices": notices,
        "total": len(notices)
    }

@router.get("/{notice_id}", response_model=Notice)
async def get_notice(
    course_id: str,
    notice_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    eclass_service: EclassService = Depends(lambda: EclassService())
) -> Any:
    """특정 공지사항 조회"""
    notices = await eclass_service.get_notices(current_user["id"], course_id, db)
    for notice in notices:
        if notice["article_id"] == notice_id:
            return notice
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="공지사항을 찾을 수 없습니다"
    )

@router.post("/refresh")
async def refresh_notices(
    course_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    eclass_service: EclassService = Depends(lambda: EclassService())
) -> Any:
    """공지사항 새로고침"""
    result = await eclass_service.crawl_course(current_user["id"], course_id, db)
    
    # 새로운 공지사항 조회
    notices = await eclass_service.get_notices(current_user["id"], course_id, db)
    
    return {
        "notices": notices,
        "total": len(notices),
        "message": "공지사항 새로고침이 완료되었습니다",
        "crawl_result": result
    }
