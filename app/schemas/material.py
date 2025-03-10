from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

class MaterialBase(BaseModel):
    article_id: str
    title: str
    content: Optional[str] = None
    author: Optional[str] = None
    date: Optional[str] = None
    views: Optional[int] = 0

class MaterialCreate(MaterialBase):
    course_id: str

class MaterialUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    date: Optional[str] = None
    views: Optional[int] = None

class MaterialInDBBase(MaterialBase):
    id: int
    course_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class Material(MaterialInDBBase):
    attachments: Optional[List[Any]] = []

class MaterialList(BaseModel):
    materials: List[Material]
    total: int
