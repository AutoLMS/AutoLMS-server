from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CourseBase(BaseModel):
    id: str
    name: str
    code: Optional[str] = None
    time: Optional[str] = None

class CourseCreate(CourseBase):
    user_id: str

class CourseUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    time: Optional[str] = None

class CourseInDBBase(CourseBase):
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class Course(CourseInDBBase):
    pass

class CourseList(BaseModel):
    courses: List[Course]
    total: int
