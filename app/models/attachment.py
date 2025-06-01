from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base

class Attachment(Base):
    """첨부파일 메타데이터 - 실제 Supabase 스키마에 맞춤"""
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)  # UUID 타입, NOT NULL
    course_id = Column(String, nullable=False)  # NOT NULL, foreign key
    related_type = Column(String, nullable=False)  # NOT NULL
    related_id = Column(Integer, nullable=False)  # NOT NULL
    original_filename = Column(String, nullable=False)  # NOT NULL
    stored_filename = Column(String, nullable=False)  # NOT NULL
    file_size = Column(BigInteger)  # nullable
    file_type = Column(String)  # nullable
    download_url = Column(String)  # nullable
    storage_path = Column(String)  # nullable
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    file_name = Column(String)  # nullable
    original_url = Column(String)  # nullable
    source_id = Column(String)  # nullable
    source_type = Column(String)  # nullable

    def to_dict(self) -> dict:
        """Convert model instance to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'course_id': self.course_id,
            'related_type': self.related_type,
            'related_id': self.related_id,
            'original_filename': self.original_filename,
            'stored_filename': self.stored_filename,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'download_url': self.download_url,
            'storage_path': self.storage_path,
            'file_name': self.file_name,
            'original_url': self.original_url,
            'source_id': self.source_id,
            'source_type': self.source_type,
            'file_url': self.download_url or self.storage_path,  # For compatibility
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
