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

    # 관계 정의
    course = relationship("Course", back_populates="assignments")
    attachments = relationship("Attachment", back_populates="assignment")

    def to_dict(self) -> dict:
        """모델을 딕셔너리로 변환"""
        return {
            'id': self.id,
            'article_id': self.article_id,
            'course_id': self.course_id,
            'title': self.title,
            'content': self.content,
            'due_date': self.due_date,
            'status': self.status,
            'submission_status': self.submission_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'attachments': [attachment.to_dict() for attachment in self.attachments] if self.attachments else []
        }