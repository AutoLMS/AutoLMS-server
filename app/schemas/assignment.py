from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class AssignmentBase(BaseModel):
    """과제 기본 스키마 - Supabase assignments 테이블 구조에 맞춤"""
    assignment_id: str  # 과제 고유 ID (e-Class에서)
    title: str  # 과제 제목
    content: Optional[str] = None  # 과제 내용
    due_date: Optional[str] = None  # 제출 마감일 (e-Class 형식)
    status: Optional[str] = None  # 과제 상태
    submission_status: Optional[str] = None  # 제출 상태
    article_id: Optional[str] = None  # 게시글 ID (e-Class)


class AssignmentCreate(AssignmentBase):
    """과제 생성 요청 스키마"""
    user_id: str  # 사용자 ID (필수)
    course_id: str  # 강의 ID (필수)


class AssignmentUpdate(BaseModel):
    """과제 업데이트 스키마"""
    title: Optional[str] = None
    content: Optional[str] = None
    due_date: Optional[str] = None
    status: Optional[str] = None
    submission_status: Optional[str] = None
    has_attachments: Optional[bool] = None
    attachments: Optional[List[Any]] = None


class AssignmentInDBBase(AssignmentBase):
    """데이터베이스의 과제 스키마 (내부 필드 포함)"""
    id: int  # Primary key (auto increment)
    user_id: str  # 사용자 ID (FK to auth.users.id)
    course_id: str  # 강의 ID
    has_attachments: Optional[bool] = False  # 첨부파일 존재 여부
    attachments: Optional[List[Any]] = None  # 첨부파일 정보 (JSONB)
    created_at: datetime  # 생성 시간
    updated_at: datetime  # 수정 시간
    
    class Config:
        from_attributes = True


class Assignment(AssignmentInDBBase):
    """API 응답용 과제 스키마"""
    pass


class AssignmentOut(BaseModel):
    """과제 출력 스키마 (사용자에게 반환)"""
    id: int
    assignment_id: str
    title: str
    content: Optional[str] = None
    due_date: Optional[str] = None
    status: Optional[str] = None
    submission_status: Optional[str] = None
    course_id: str
    has_attachments: Optional[bool] = False
    attachments: Optional[List[Any]] = None
    created_at: datetime
    updated_at: datetime


class AssignmentList(BaseModel):
    """과제 목록 응답 스키마"""
    assignments: List[AssignmentOut]
    total: int


class AssignmentWithCourse(AssignmentOut):
    """강의 정보가 포함된 과제 스키마"""
    course_name: Optional[str] = None
    instructor: Optional[str] = None
