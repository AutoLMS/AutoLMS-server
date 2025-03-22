from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class Course(Base):
    """강의 정보"""
    __tablename__ = "courses"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    code = Column(String)
    time = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="courses")

    def __repr__(self):
        return f"<Course(id={self.id}, name={self.name})>"