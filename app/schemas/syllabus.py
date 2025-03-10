from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from datetime import datetime

class SyllabusBase(BaseModel):
    year_semester: Optional[str] = None
    course_type: Optional[str] = None
    professor_name: Optional[str] = None
    office_hours: Optional[str] = None
    homepage: Optional[str] = None
    course_overview: Optional[str] = None
    objectives: Optional[str] = None
    textbooks: Optional[str] = None
    equipment: Optional[str] = None
    evaluation_method: Optional[str] = None
    weekly_plans: Optional[Dict[str, Any]] = None

class SyllabusCreate(SyllabusBase):
    course_id: str

class SyllabusUpdate(SyllabusBase):
    pass

class SyllabusInDBBase(SyllabusBase):
    id: int
    course_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class Syllabus(SyllabusInDBBase):
    pass
