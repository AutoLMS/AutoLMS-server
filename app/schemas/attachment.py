from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class AttachmentBase(BaseModel):
    source_type: str
    source_id: str
    file_name: str
    file_size: Optional[int] = None
    content_type: Optional[str] = None
    storage_path: str
    file_url: Optional[str] = None

class AttachmentCreate(AttachmentBase):
    user_id: str

class AttachmentUpdate(BaseModel):
    file_url: Optional[str] = None
    expires_at: Optional[datetime] = None

class AttachmentInDBBase(AttachmentBase):
    id: int
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class Attachment(AttachmentInDBBase):
    pass

class AttachmentList(BaseModel):
    attachments: List[Attachment]
    total: int
