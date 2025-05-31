from sqlalchemy import Column, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base

class UserCourse(Base):
    """사용자와 강의의 관계"""
    __tablename__ = "user_courses"
    
    user_id = Column(String, ForeignKey("users.id"), primary_key=True)
    course_id = Column(String, ForeignKey("courses.id"), primary_key=True)
    semester = Column(String)
    time = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
