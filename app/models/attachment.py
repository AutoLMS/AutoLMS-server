from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base

class Attachment(Base):
    """첨부파일 메타데이터"""
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_type = Column(String, nullable=False)  # 'notice', 'material', 'assignment'
    source_id = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_size = Column(BigInteger)
    content_type = Column(String)
    storage_path = Column(String, nullable=False)
    original_url = Column(String)
    # Removed user_id field to match Supabase schema
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계 정의 - polymorphic
    notice_id = Column(Integer, ForeignKey("notices.id"))
    material_id = Column(Integer, ForeignKey("materials.id"))
    assignment_id = Column(Integer, ForeignKey("assignments.id"))
    
    notice = relationship("Notice", back_populates="attachments")
    material = relationship("Material", back_populates="attachments")
    assignment = relationship("Assignment", back_populates="attachments")

    def to_dict(self) -> dict:
        """모델을 딕셔너리로 변환"""
        return {
            'id': self.id,
            'source_type': self.source_type,
            'source_id': self.source_id,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'content_type': self.content_type,
            'storage_path': self.storage_path,
            'original_url': self.original_url,
            'file_url': self.storage_path,  # For compatibility, provide file_url as storage_path
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
