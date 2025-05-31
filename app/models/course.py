from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base

class Course(Base):
    """강의 정보"""
    __tablename__ = "courses"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)  # Added user_id field
    name = Column(String, nullable=False)
    code = Column(String)
    time = Column(String)  # Changed from semester to time to match Supabase schema
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """모델을 딕셔너리로 변환"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'code': self.code,
            'time': self.time,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
