from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class NoticeBase(BaseModel):
    """공지사항 기본 스키마 - Supabase notices 테이블 구조에 맞춤"""
    notice_id: str  # 공지사항 고유 ID (e-Class에서)
    title: str  # 공지사항 제목
    content: Optional[str] = None  # 공지사항 내용
    author: Optional[str] = None  # 작성자
    date: Optional[str] = None  # 작성일 (e-Class 형식)
    views: Optional[int] = 0  # 조회수
    article_id: Optional[str] = None  # 게시글 ID (e-Class)


class NoticeCreate(NoticeBase):
    """공지사항 생성 요청 스키마"""
    user_id: str  # 사용자 ID (필수)
    course_id: str  # 강의 ID (필수)


class NoticeUpdate(BaseModel):
    """공지사항 업데이트 스키마"""
    title: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None
    date: Optional[str] = None
    views: Optional[int] = None
    has_attachments: Optional[bool] = None
    attachments: Optional[List[Any]] = None


class NoticeInDBBase(NoticeBase):
    """데이터베이스의 공지사항 스키마 (내부 필드 포함)"""
    id: int  # Primary key (auto increment)
    user_id: str  # 사용자 ID (FK to auth.users.id)
    course_id: str  # 강의 ID
    has_attachments: Optional[bool] = False  # 첨부파일 존재 여부
    attachments: Optional[List[Any]] = None  # 첨부파일 정보 (JSONB)
    created_at: datetime  # 생성 시간
    updated_at: datetime  # 수정 시간
    
    class Config:
        from_attributes = True


class Notice(NoticeInDBBase):
    """API 응답용 공지사항 스키마"""
    pass


class NoticeOut(BaseModel):
    """공지사항 출력 스키마 (사용자에게 반환)"""
    id: int
    notice_id: str
    title: str
    content: Optional[str] = None
    author: Optional[str] = None
    date: Optional[str] = None
    views: Optional[int] = 0
    course_id: str
    has_attachments: Optional[bool] = False
    attachments: Optional[List[Any]] = None
    created_at: datetime
    updated_at: datetime


class NoticeList(BaseModel):
    """공지사항 목록 응답 스키마"""
    notices: List[NoticeOut]
    total: int


class NoticeWithCourse(NoticeOut):
    """강의 정보가 포함된 공지사항 스키마"""
    course_name: Optional[str] = None
    instructor: Optional[str] = None
