from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base

class Syllabus(Base):
    """강의 계획서"""
    __tablename__ = "syllabus"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(String, ForeignKey("courses.id"), unique=True)
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
    
    # 관계 정의
    course = relationship("Course", back_populates="syllabus")

    def to_dict(self) -> dict:
        """모델을 딕셔너리로 변환"""
        return {
            'id': self.id,
            'course_id': self.course_id,
            'year_semester': self.year_semester,
            'course_type': self.course_type,
            'professor_name': self.professor_name,
            'office_hours': self.office_hours,
            'homepage': self.homepage,
            'course_overview': self.course_overview,
            'objectives': self.objectives,
            'textbooks': self.textbooks,
            'equipment': self.equipment,
            'evaluation_method': self.evaluation_method,
            'weekly_plans': self.weekly_plans,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }