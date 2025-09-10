from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base
from app.models.user_courses import user_courses

class Course(Base):
    """강의 정보"""
    __tablename__ = "courses"

    id = Column(String, primary_key=True)  # e-Class course_id
    name = Column(String, nullable=False)
    code = Column(String)
    semester = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계 정의 - User 모델 제거로 인해 주석 처리
    notices = relationship("Notice", back_populates="course")
    materials = relationship("Material", back_populates="course")
    assignments = relationship("Assignment", back_populates="course")
    syllabus = relationship("Syllabus", back_populates="course", uselist=False)

    def to_dict(self) -> dict:
        """강의 모델을 딕셔너리로 변환"""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'semester': self.semester,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }