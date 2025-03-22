from typing import AsyncGenerator
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import AsyncSessionLocal
from app.services.auth_service import AuthService
from app.services.core import SessionService
from app.services.content import (
    CourseService,
    NoticeService,
    MaterialService,
    AssignmentService,
    SyllabusService
)
from app.services.storage import StorageService
from app.services.parsers import (
    CourseParser,
    NoticeParser,
    MaterialParser,
    AssignmentParser,
    SyllabusParser
)
from app.core.supabase_client import get_supabase_client
from app.db.repositories.course_repository import CourseRepository
from app.db.repositories.notice_repository import NoticeRepository
from app.db.repositories.material_repository import MaterialRepository
from app.db.repositories.assignment_repository import AssignmentRepository
from app.db.repositories.attachment_repository import AttachmentRepository
from app.db.repositories.syllabus_repository import SyllabusRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

# 싱글톤 인스턴스
_session_service = None
_storage_service = None
_course_service = None
_notice_service = None
_material_service = None
_assignment_service = None
_syllabus_service = None

def get_auth_service() -> AuthService:
    """인증 서비스 제공"""
    return AuthService(get_supabase_client())

# 파서 의존성
def get_course_parser() -> CourseParser:
    """CourseParser 제공"""
    return CourseParser()

def get_notice_parser() -> NoticeParser:
    """NoticeParser 제공"""
    return NoticeParser()

def get_material_parser() -> MaterialParser:
    """MaterialParser 제공"""
    return MaterialParser()

def get_assignment_parser() -> AssignmentParser:
    """AssignmentParser 제공"""
    return AssignmentParser()

def get_syllabus_parser() -> SyllabusParser:
    """SyllabusParser 제공"""
    return SyllabusParser()

# 리포지토리 의존성
def get_course_repository() -> CourseRepository:
    """CourseRepository 제공"""
    return CourseRepository()

def get_notice_repository() -> NoticeRepository:
    """NoticeRepository 제공"""
    return NoticeRepository()

def get_material_repository() -> MaterialRepository:
    """MaterialRepository 제공"""
    return MaterialRepository()

def get_assignment_repository() -> AssignmentRepository:
    """AssignmentRepository 제공"""
    return AssignmentRepository()

def get_attachment_repository() -> AttachmentRepository:
    """AttachmentRepository 제공"""
    return AttachmentRepository()

def get_syllabus_repository() -> SyllabusRepository:
    """SyllabusRepository 제공"""
    return SyllabusRepository()

# 기본 서비스 의존성
def get_session_service() -> SessionService:
    """SessionService 제공 (싱글톤)"""
    global _session_service
    if not _session_service:
        _session_service = SessionService()
    return _session_service

def get_storage_service() -> StorageService:
    """StorageService 제공 (싱글톤)"""
    global _storage_service
    if not _storage_service:
        _storage_service = StorageService()
    return _storage_service

# 콘텐츠 서비스 의존성
def get_course_service(
    session_service: SessionService = Depends(get_session_service),
    course_parser: CourseParser = Depends(get_course_parser),
    course_repository: CourseRepository = Depends(get_course_repository)
) -> CourseService:
    """CourseService 제공 (싱글톤)"""
    global _course_service
    if not _course_service:
        _course_service = CourseService(
            session_service=session_service,
            course_parser=course_parser,
            course_repository=course_repository
        )
    return _course_service

def get_notice_service(
    session_service: SessionService = Depends(get_session_service),
    notice_parser: NoticeParser = Depends(get_notice_parser),
    notice_repository: NoticeRepository = Depends(get_notice_repository),
    attachment_repository: AttachmentRepository = Depends(get_attachment_repository),
    storage_service: StorageService = Depends(get_storage_service)
) -> NoticeService:
    """NoticeService 제공 (싱글톤)"""
    global _notice_service
    if not _notice_service:
        _notice_service = NoticeService(
            session_service=session_service,
            notice_parser=notice_parser,
            notice_repository=notice_repository,
            attachment_repository=attachment_repository,
            storage_service=storage_service
        )
    return _notice_service

def get_material_service(
    session_service: SessionService = Depends(get_session_service),
    material_parser: MaterialParser = Depends(get_material_parser),
    material_repository: MaterialRepository = Depends(get_material_repository),
    attachment_repository: AttachmentRepository = Depends(get_attachment_repository),
    storage_service: StorageService = Depends(get_storage_service)
) -> MaterialService:
    """MaterialService 제공 (싱글톤)"""
    global _material_service
    if not _material_service:
        _material_service = MaterialService(
            session_service=session_service,
            material_parser=material_parser,
            material_repository=material_repository,
            attachment_repository=attachment_repository,
            storage_service=storage_service
        )
    return _material_service

def get_assignment_service(
    session_service: SessionService = Depends(get_session_service),
    assignment_parser: AssignmentParser = Depends(get_assignment_parser),
    assignment_repository: AssignmentRepository = Depends(get_assignment_repository),
    attachment_repository: AttachmentRepository = Depends(get_attachment_repository),
    storage_service: StorageService = Depends(get_storage_service)
) -> AssignmentService:
    """AssignmentService 제공 (싱글톤)"""
    global _assignment_service
    if not _assignment_service:
        _assignment_service = AssignmentService(
            session_service=session_service,
            assignment_parser=assignment_parser,
            assignment_repository=assignment_repository,
            attachment_repository=attachment_repository,
            storage_service=storage_service
        )
    return _assignment_service

def get_syllabus_service(
    session_service: SessionService = Depends(get_session_service),
    syllabus_parser: SyllabusParser = Depends(get_syllabus_parser),
    syllabus_repository: SyllabusRepository = Depends(get_syllabus_repository)
) -> SyllabusService:
    """SyllabusService 제공 (싱글톤)"""
    global _syllabus_service
    if not _syllabus_service:
        _syllabus_service = SyllabusService(
            session_service=session_service,
            syllabus_parser=syllabus_parser,
            syllabus_repository=syllabus_repository
        )
    return _syllabus_service

# 사용자 인증 의존성
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service)
):
    """현재 로그인한 사용자 확인"""
    return await auth_service.get_current_user(token)

# 데이터베이스 세션 의존성
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """데이터베이스 세션 제공"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()