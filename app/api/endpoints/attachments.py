from fastapi import APIRouter, Depends, HTTPException, status, Response
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.attachment import Attachment, AttachmentList
from app.api.deps import get_current_user, get_db_session, get_file_handler
from app.services.file_handler import FileHandler
from app.db.repositories.attachment_repository import AttachmentRepository

router = APIRouter()

@router.get("/{attachment_id}", response_model=Attachment)
async def get_attachment(
    attachment_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
) -> Any:
    """첨부파일 메타데이터 조회"""
    attachment_repo = AttachmentRepository()
    
    attachment = await attachment_repo.get_by_id(attachment_id)
    if not attachment or attachment.user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="첨부파일을 찾을 수 없습니다"
        )
    
    return attachment.to_dict()

@router.get("/{attachment_id}/download")
async def download_attachment(
    attachment_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user),
    file_handler: FileHandler = Depends(get_file_handler)
) -> Any:
    """첨부파일 다운로드"""
    attachment_repo = AttachmentRepository(db)
    
    attachment = await attachment_repo.get_by_id(attachment_id)
    if not attachment or attachment.user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="첨부파일을 찾을 수 없습니다"
        )
    
    # 스토리지 URL이 있으면 리다이렉션
    if attachment.storage_url:
        return Response(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": attachment.storage_url}
        )
    
    # 로컬 파일이 있으면 반환
    elif attachment.local_path:
        import os
        if os.path.exists(attachment.local_path):
            with open(attachment.local_path, 'rb') as f:
                file_data = f.read()
            
            response = Response(content=file_data)
            response.headers["Content-Disposition"] = f'attachment; filename="{attachment.name}"'
            response.headers["Content-Type"] = "application/octet-stream"
            return response
    
    # 파일을 찾을 수 없음
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="파일을 찾을 수 없습니다"
    )

@router.get("/by-source/{source_type}/{source_id}", response_model=AttachmentList)
async def get_attachments_by_source(
    source_type: str,
    source_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
) -> Any:
    """소스별 첨부파일 목록 조회"""
    attachment_repo = AttachmentRepository(db)
    
    attachments = await attachment_repo.get_by_source(source_id, source_type)
    
    # 사용자 ID로 필터링
    attachments = [a for a in attachments if a.user_id == current_user["id"]]
    
    return {
        "attachments": [attachment.to_dict() for attachment in attachments],
        "total": len(attachments)
    }

@router.get("/search/", response_model=AttachmentList)
async def search_attachments(
    query: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
) -> Any:
    """첨부파일 검색"""
    attachment_repo = AttachmentRepository(db)
    
    attachments = await attachment_repo.search(query, user_id=current_user["id"])
    
    return {
        "attachments": [attachment.to_dict() for attachment in attachments],
        "total": len(attachments)
    }
