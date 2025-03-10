from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base

class Assignment(Base):
    """과제"""
    __tablename__ = "assignments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(String, nullable=False)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text)
    due_date = Column(String)
    status = Column(String)
    submission_status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
