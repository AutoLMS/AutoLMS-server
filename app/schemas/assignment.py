from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

class AssignmentBase(BaseModel):
    article_id: str
    title: str
    content: Optional[str] = None
    due_date: Optional[str] = None
    status: Optional[str] = None
    submission_status: Optional[str] = None

class AssignmentCreate(AssignmentBase):
    course_id: str

class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    due_date: Optional[str] = None
    status: Optional[str] = None
    submission_status: Optional[str] = None

class AssignmentInDBBase(AssignmentBase):
    id: int
    course_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class Assignment(AssignmentInDBBase):
    attachments: Optional[List[Any]] = []

class AssignmentList(BaseModel):
    assignments: List[Assignment]
    total: int
