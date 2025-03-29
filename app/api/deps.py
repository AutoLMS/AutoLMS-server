from typing import Generator, Optional, Any, AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import AsyncSessionLocal
from app.services import CrawlService, auth_service
from app.services.auth_service import AuthService

from app.services.content import (
    CourseService,
    NoticeService,
    MaterialService,
    AssignmentService,
    SyllabusService,
)
from app.services.session import AuthSessionService, EclassSessionManager
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
_auth_session_service = None
_eclass_session_manager = None
_storage_service = None
_course_service = None
_notice_service = None
_auth_service = None
_material_service = None
_assignment_service = None
_syllabus_service = None
_crawl_service = None

# 세션 서비스 의존성
def get_auth_session_service() -> AuthSessionService:
    """앱 인증 세션 서비스 제공"""
    global _auth_session_service
    if not _auth_session_service:
        _auth_session_service = AuthSessionService()
    return _auth_session_service

def get_eclass_session_manager() -> EclassSessionManager:
    """이클래스 세션 관리자 제공"""
    global _eclass_session_manager
    if not _eclass_session_manager:
        _eclass_session_manager = EclassSessionManager()
    return _eclass_session_manager

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
def get_storage_service() -> StorageService:
    """StorageService 제공 (싱글톤)"""
    global _storage_service
    if not _storage_service:
        _storage_service = StorageService()
    return _storage_service

# 콘텐츠 서비스 의존성
def get_course_service(
    eclass_session_manager: EclassSessionManager = Depends(get_eclass_session_manager),
    course_parser: CourseParser = Depends(get_course_parser),
    course_repository: CourseRepository = Depends(get_course_repository)
) -> CourseService:
    """CourseService 제공 (싱글톤)"""
    global _course_service
    if not _course_service:
        _course_service = CourseService(
            session_service=eclass_session_manager,
            course_parser=course_parser,
            course_repository=course_repository
        )
    return _course_service

def get_notice_service(
    eclass_session_manager: EclassSessionManager = Depends(get_eclass_session_manager),
    notice_parser: NoticeParser = Depends(get_notice_parser),
    notice_repository: NoticeRepository = Depends(get_notice_repository),
    attachment_repository: AttachmentRepository = Depends(get_attachment_repository),
    storage_service: StorageService = Depends(get_storage_service)
) -> NoticeService:
    """NoticeService 제공 (싱글톤)"""
    global _notice_service
    if not _notice_service:
        _notice_service = NoticeService(
            eclass_session=eclass_session_manager,
            notice_parser=notice_parser,
            notice_repository=notice_repository,
            attachment_repository=attachment_repository,
            storage_service=storage_service
        )
    return _notice_service

def get_material_service(
    eclass_session_manager: EclassSessionManager = Depends(get_eclass_session_manager),
    material_parser: MaterialParser = Depends(get_material_parser),
    material_repository: MaterialRepository = Depends(get_material_repository),
    attachment_repository: AttachmentRepository = Depends(get_attachment_repository),
    storage_service: StorageService = Depends(get_storage_service),
    auth_service: AuthService = Depends(get_auth_service)
) -> MaterialService:
    """MaterialService 제공 (싱글톤)"""
    global _material_service
    if not _material_service:
        _material_service = MaterialService(
            eclass_session=eclass_session_manager,
            material_parser=material_parser,
            material_repository=material_repository,
            attachment_repository=attachment_repository,
            storage_service=storage_service,
            auth_service=auth_service
        )
    return _material_service

def get_assignment_service(
    eclass_session_manager: EclassSessionManager = Depends(get_eclass_session_manager),
    assignment_parser: AssignmentParser = Depends(get_assignment_parser),
    assignment_repository: AssignmentRepository = Depends(get_assignment_repository),
    attachment_repository: AttachmentRepository = Depends(get_attachment_repository),
    storage_service: StorageService = Depends(get_storage_service)
) -> AssignmentService:
    """AssignmentService 제공 (싱글톤)"""
    global _assignment_service
    if not _assignment_service:
        _assignment_service = AssignmentService(
            session_service=eclass_session_manager,
            assignment_parser=assignment_parser,
            assignment_repository=assignment_repository,
            attachment_repository=attachment_repository,
        )
    return _assignment_service

def get_syllabus_service(
    eclass_session_manager: EclassSessionManager = Depends(get_eclass_session_manager),
    syllabus_parser: SyllabusParser = Depends(get_syllabus_parser),
    syllabus_repository: SyllabusRepository = Depends(get_syllabus_repository),
    auth_service: AuthService = Depends(get_auth_service)
) -> SyllabusService:
    """SyllabusService 제공 (싱글톤)"""
    global _syllabus_service
    if not _syllabus_service:
        _syllabus_service = SyllabusService(
            eclass_session=eclass_session_manager,
            syllabus_parser=syllabus_parser,
            syllabus_repository=syllabus_repository,
            auth_service=auth_service
        )
    return _syllabus_service

#크롤러 의존성
def get_crawl_service(
    eclass_session: EclassSessionManager = Depends(get_eclass_session_manager),
    course_service: CourseService = Depends(get_course_service),
    notice_service: NoticeService = Depends(get_notice_service),
    material_service: MaterialService = Depends(get_material_service),
    assignment_service: AssignmentService = Depends(get_assignment_service),
    syllabus_service: SyllabusService = Depends(get_syllabus_service)
) -> CrawlService:
    """CrawlService 제공 (싱글톤)"""
    global _crawl_service
    if not _crawl_service:
        _crawl_service = CrawlService(
            eclass_session=eclass_session,
            course_service=course_service,
            notice_service=notice_service,
            material_service=material_service,
            assignment_service=assignment_service,
            syllabus_service=syllabus_service
        )
    return _crawl_service




# 사용자 인증 의존성
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_session_service: AuthSessionService = Depends(get_auth_session_service)
):
    """현재 로그인한 사용자 확인"""
    user_info = await auth_session_service.verify_token(token)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 인증 정보",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_info

# 데이터베이스 세션 의존성
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """데이터베이스 세션 제공"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()