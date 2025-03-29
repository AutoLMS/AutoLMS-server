from sqlalchemy import Table, Column, String, DateTime, ForeignKey
from datetime import datetime

from app.db.base import Base

# 다대다 관계 테이블
user_courses = Table(
    'user_courses',
    Base.metadata,
    Column('user_id', String, ForeignKey('users.id'), primary_key=True),
    Column('course_id', String, ForeignKey('courses.id'), primary_key=True),
    Column('semester', String),
    Column('time', String),
    Column('created_at', DateTime, default=datetime.utcnow),
    Column('updated_at', DateTime, onupdate=datetime.utcnow)
)