from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any, List

from app.schemas.attachment import Attachment, AttachmentList
from app.api.deps import (
    get_current_user,
    get_attachment_repository,
    get_storage_service
)
from app.db.repositories.attachment_repository import AttachmentRepository
from app.services.storage.storage_service import StorageService

router = APIRouter()


@router.get("/{attachment_id}/download")
async def get_download_url(
        attachment_id: int,
        current_user: dict = Depends(get_current_user),
        attachment_repository: AttachmentRepository = Depends(get_attachment_repository),
        storage_service: StorageService = Depends(get_storage_service)
) -> Any:
    """첨부파일 다운로드 URL 조회"""
    # 첨부파일 조회
    attachment = await attachment_repository.get_by_id(str(attachment_id))
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="첨부파일을 찾을 수 없습니다."
        )
    
    # Supabase Storage에서 다운로드 URL 생성
    download_url = await storage_service.get_file_url(attachment['storage_path'])
    if not download_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="파일 URL을 생성할 수 없습니다."
        )
    return {"download_url": download_url}


@router.get("/{source_type}/{source_id}", response_model=AttachmentList)
async def get_attachments(
        source_type: str,
        source_id: int,
        current_user: dict = Depends(get_current_user),
        attachment_repository: AttachmentRepository = Depends(get_attachment_repository)
) -> Any:
    """특정 출처(공지사항, 강의자료, 과제 등)의 첨부파일 목록 조회"""
    attachments = await attachment_repository.get_by_source(str(source_id), source_type)

    return {
        "attachments": attachments,
        "total": len(attachments)
    }


@router.get("/search", response_model=AttachmentList)
async def search_attachments(
        query: str,
        current_user: dict = Depends(get_current_user),
        attachment_repository: AttachmentRepository = Depends(get_attachment_repository)
) -> Any:
    """첨부파일 검색"""
    # 파일명으로 검색 (간단한 구현)
    all_attachments = await attachment_repository.get_all()
    attachments = [att for att in all_attachments if query.lower() in att.get('file_name', '').lower()]
    return {
        "attachments": attachments,
        "total": len(attachments)
    }


@router.get("/{attachment_id}", response_model=Attachment)
async def get_attachment(
        attachment_id: int,
        current_user: dict = Depends(get_current_user),
        attachment_repository: AttachmentRepository = Depends(get_attachment_repository)
) -> Any:
    """특정 첨부파일 메타데이터 조회"""
    attachment = await attachment_repository.get_by_id(str(attachment_id))
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="첨부파일을 찾을 수 없습니다."
        )
    return attachment