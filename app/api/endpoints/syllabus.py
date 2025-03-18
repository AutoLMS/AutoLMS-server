from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from app.api.deps import get_current_user, get_db_session
from app.services.eclass_service import EclassService

router = APIRouter()

@router.get("", response_model=Dict[str, Any])
async def get_syllabus(
    course_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """강의계획서 조회"""
    try:
        eclass_service = EclassService()
        syllabus = await eclass_service.get_syllabus(current_user["id"], course_id, db)
        return syllabus
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))