from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class CourseBase(BaseModel):
    """강의 기본 스키마 - Supabase courses 테이블 구조에 맞춤"""
    course_id: str  # 실제 강의 고유 ID (e-Class에서)
    course_name: str  # 강의명
    instructor: Optional[str] = None  # 교수명
    semester: Optional[str] = None  # 학기
    year: Optional[int] = None  # 연도
    description: Optional[str] = None  # 강의 설명


class CourseCreate(CourseBase):
    """강의 생성 요청 스키마"""
    pass


class CourseUpdate(BaseModel):
    """강의 업데이트 스키마"""
    course_name: Optional[str] = None
    instructor: Optional[str] = None
    semester: Optional[str] = None
    year: Optional[int] = None
    description: Optional[str] = None
    last_crawled: Optional[datetime] = None


class CourseInDBBase(CourseBase):
    """데이터베이스의 강의 스키마 (내부 필드 포함)"""
    id: str  # UUID primary key
    last_crawled: Optional[datetime] = None  # 마지막 크롤링 시간
    created_at: datetime  # 생성 시간
    updated_at: datetime  # 수정 시간
    
    class Config:
        from_attributes = True


class Course(CourseInDBBase):
    """API 응답용 강의 스키마"""
    pass


class CourseOut(BaseModel):
    """강의 출력 스키마 (사용자에게 반환)"""
    id: str
    course_id: str
    course_name: str
    instructor: Optional[str] = None
    semester: Optional[str] = None
    year: Optional[int] = None
    description: Optional[str] = None
    last_crawled: Optional[datetime] = None


class CourseList(BaseModel):
    """강의 목록 응답 스키마"""
    courses: List[CourseOut]
    total: int


class UserCourseRelation(BaseModel):
    """사용자-강의 연결 관계 스키마"""
    id: str  # user_courses 테이블 UUID
    user_id: str  # 사용자 ID
    course_id: str  # 강의 course_id
    enrollment_date: Optional[datetime] = None  # 등록일
    last_accessed: Optional[datetime] = None  # 마지막 접근일
    created_at: datetime
    updated_at: datetime


class CourseWithEnrollment(CourseOut):
    """등록 정보가 포함된 강의 스키마"""
    enrollment_date: Optional[datetime] = None
    last_accessed: Optional[datetime] = None