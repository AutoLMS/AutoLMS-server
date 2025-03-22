from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.orm import relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    eclass_id = Column(String, nullable=True)  # 이클래스 학번
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sessions = relationship("Session", back_populates="user")
    courses = relationship("Course", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
        
    def to_dict(self) -> dict:
        """사용자 객체를 딕셔너리로 변환"""
        return {
            "id": self.id,
            "email": self.email,
            "eclass_id": self.eclass_id,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
