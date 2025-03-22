from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.attachment import Attachment, AttachmentList
from app.api.deps import (
    get_current_user,
    get_db_session,
    get_storage_service
)
from app.services.storage.storage_service import StorageService

router = APIRouter()


@router.get("/{attachment_id}/download")
async def get_download_url(
        attachment_id: int,
        db: AsyncSession = Depends(get_db_session),
        current_user: dict = Depends(get_current_user),
        storage_service: StorageService = Depends(get_storage_service)
) -> Any:
    """첨부파일 다운로드 URL 조회"""
    download_url = await storage_service.get_download_url(attachment_id, current_user["id"], db)
    if not download_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="첨부파일을 찾을 수 없습니다."
        )
    return {"download_url": download_url}


@router.get("/{source_type}/{source_id}", response_model=AttachmentList)
async def get_attachments(
        source_type: str,
        source_id: int,
        db: AsyncSession = Depends(get_db_session),
        current_user: dict = Depends(get_current_user),
        storage_service: StorageService = Depends(get_storage_service)
) -> Any:
    """특정 출처(공지사항, 강의자료, 과제 등)의 첨부파일 목록 조회"""
    attachments = await storage_service.get_attachments_by_source(
        source_type,
        source_id,
        current_user["id"],
        db
    )

    return {
        "attachments": attachments,
        "total": len(attachments)
    }


@router.get("/search", response_model=AttachmentList)
async def search_attachments(
        query: str,
        db: AsyncSession = Depends(get_db_session),
        current_user: dict = Depends(get_current_user),
        storage_service: StorageService = Depends(get_storage_service)
) -> Any:
    """첨부파일 검색"""
    attachments = await storage_service.search_attachments(query, current_user["id"], db)
    return {
        "attachments": attachments,
        "total": len(attachments)
    }


@router.get("/{attachment_id}", response_model=Attachment)
async def get_attachment(
        attachment_id: int,
        db: AsyncSession = Depends(get_db_session),
        current_user: dict = Depends(get_current_user),
        storage_service: StorageService = Depends(get_storage_service)
) -> Any:
    """특정 첨부파일 메타데이터 조회"""
    attachment = await storage_service.get_attachment(attachment_id, current_user["id"], db)
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="첨부파일을 찾을 수 없습니다."
        )
    return attachment