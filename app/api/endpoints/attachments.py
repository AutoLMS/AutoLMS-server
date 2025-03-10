from fastapi import APIRouter, Depends, HTTPException, status, Response
from typing import Any
from sqlalchemy.orm import Session

from app.schemas.attachment import Attachment, AttachmentList
from app.api.deps import get_current_user, get_db
from app.services.file_handler import FileHandler

router = APIRouter()

@router.get("/{attachment_id}", response_model=Attachment)
async def get_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Any:
    """첨부파일 메타데이터 조회"""
    # 첨부파일 리포지토리 추가 필요
    from app.db.repositories.attachment_repository import AttachmentRepository
    attachment_repo = AttachmentRepository()
    
    attachment = await attachment_repo.get_by_id(db, attachment_id)
    if not attachment or attachment.user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="첨부파일을 찾을 수 없습니다"
        )
    
    return attachment

@router.get("/{attachment_id}/download")
async def download_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    file_handler: FileHandler = Depends(lambda: FileHandler())
) -> Any:
    """첨부파일 다운로드"""
    # 첨부파일 리포지토리 추가 필요
    from app.db.repositories.attachment_repository import AttachmentRepository
    attachment_repo = AttachmentRepository()
    
    attachment = await attachment_repo.get_by_id(db, attachment_id)
    if not attachment or attachment.user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="첨부파일을 찾을 수 없습니다"
        )
    
    # 파일 데이터 가져오기
    file_data = await file_handler.get_attachment_data(attachment_id, db)
    if not file_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="파일을 찾을 수 없습니다"
        )
    
    # 응답 헤더 설정
    response = Response(content=file_data)
    response.headers["Content-Disposition"] = f'attachment; filename="{attachment.file_name}"'
    response.headers["Content-Type"] = attachment.content_type or "application/octet-stream"
    
    return response

@router.get("/by-source/{source_type}/{source_id}", response_model=AttachmentList)
async def get_attachments_by_source(
    source_type: str,
    source_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Any:
    """소스별 첨부파일 목록 조회"""
    # 첨부파일 리포지토리 추가 필요
    from app.db.repositories.attachment_repository import AttachmentRepository
    attachment_repo = AttachmentRepository()
    
    attachments = await attachment_repo.get_by_source(db, source_type, source_id)
    
    # 사용자 ID로 필터링
    attachments = [a for a in attachments if a.user_id == current_user["id"]]
    
    return {
        "attachments": attachments,
        "total": len(attachments)
    }

@router.get("/search/", response_model=AttachmentList)
async def search_attachments(
    query: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> Any:
    """첨부파일 검색"""
    # 첨부파일 리포지토리 추가 필요
    from app.db.repositories.attachment_repository import AttachmentRepository
    attachment_repo = AttachmentRepository()
    
    attachments = await attachment_repo.search(db, current_user["id"], query)
    
    return {
        "attachments": attachments,
        "total": len(attachments)
    }
