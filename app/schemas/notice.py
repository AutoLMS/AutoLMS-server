from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

class NoticeBase(BaseModel):
    article_id: str
    title: str
    content: Optional[str] = None
    author: Optional[str] = None
    date: Optional[str] = None
    views: Optional[int] = 0

class NoticeCreate(NoticeBase):
    course_id: str

class NoticeUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    date: Optional[str] = None
    views: Optional[int] = None

class NoticeInDBBase(NoticeBase):
    id: int
    course_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class Notice(NoticeInDBBase):
    attachments: Optional[List[Any]] = []

class NoticeList(BaseModel):
    notices: List[Notice]
    total: int
