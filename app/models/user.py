from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class User(Base):
    """사용자 정보"""
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    
    # e-Class 관련 정보 (메인 식별자)
    eclass_username = Column(String, unique=True, index=True, nullable=False)  # 학번
    # eclass_password는 Supabase에서 암호화하여 관리

    # 상태 정보
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계 정의
    courses = relationship("Course", secondary="user_courses", back_populates="users")
    sessions = relationship("Session", back_populates="user")

    def to_dict(self) -> dict:
        """사용자 모델을 딕셔너리로 변환"""
        return {
            'id': self.id,
            'eclass_username': self.eclass_username,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'courses': [course.to_dict() for course in self.courses] if self.courses else []
        }

