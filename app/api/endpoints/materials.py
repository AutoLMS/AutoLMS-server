from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.material import Material, MaterialList
from app.api.deps import get_current_user, get_db_session, get_eclass_service
from app.services.eclass_service import EclassService

router = APIRouter()

@router.get("/", response_model=MaterialList)
async def get_materials(
    course_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user),
    eclass_service: EclassService = Depends(get_eclass_service)
) -> Any:
    """강의자료 목록 조회"""
    materials = await eclass_service.get_materials(current_user["id"], course_id, db)
    return {
        "materials": materials,
        "total": len(materials)
    }

@router.get("/{material_id}", response_model=Material)
async def get_material(
    course_id: str,
    material_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user),
    eclass_service: EclassService = Depends(get_eclass_service)
) -> Any:
    """특정 강의자료 조회"""
    materials = await eclass_service.get_materials(current_user["id"], course_id, db)
    for material in materials:
        if material["article_id"] == material_id:
            return material
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="강의자료를 찾을 수 없습니다"
    )

@router.post("/refresh")
async def refresh_materials(
    course_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user),
    eclass_service: EclassService = Depends(get_eclass_service)
) -> Any:
    """강의자료 새로고침"""
    result = await eclass_service.crawl_course(current_user["id"], course_id, db)
    
    # 새로운 강의자료 조회
    materials = await eclass_service.get_materials(current_user["id"], course_id, db)
    
    return {
        "materials": materials,
        "total": len(materials),
        "message": "강의자료 새로고침이 완료되었습니다",
        "crawl_result": result
    }
