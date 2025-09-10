from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base
from app.models.user_courses import user_courses


class User(Base):
    """사용자 정보 - Supabase auth.users와 연동"""
    __tablename__ = "users"

    id = Column(String, primary_key=True)  # Supabase auth.users.id와 동일
    eclass_username = Column(String, unique=True, nullable=False)  # e-Class 사용자명
    email = Column(String)  # 이메일 (Supabase에서 관리)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 암호화된 e-Class 비밀번호 저장
    encrypted_eclass_password = Column(Text)  # 암호화된 비밀번호

    # 다대다 관계: 사용자 <-> 강의
    courses = relationship(
        "Course",
        secondary=user_courses,
        back_populates="users"
    )

    def to_dict(self) -> dict:
        """사용자 모델을 딕셔너리로 변환"""
        return {
            'id': self.id,
            'eclass_username': self.eclass_username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f"<User(id='{self.id}', eclass_username='{self.eclass_username}')>"