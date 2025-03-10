from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base

class Syllabus(Base):
    """강의 계획서"""
    __tablename__ = "syllabus"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False, unique=True)
    year_semester = Column(String)
    course_type = Column(String)
    professor_name = Column(String)
    office_hours = Column(String)
    homepage = Column(String)
    course_overview = Column(Text)
    objectives = Column(Text)
    textbooks = Column(Text)
    equipment = Column(Text)
    evaluation_method = Column(Text)
    weekly_plans = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
