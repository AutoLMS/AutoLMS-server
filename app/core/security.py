import logging
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.db.repositories.attachment_repository import AttachmentRepository
from app.db.repositories.course_repository import CourseRepository

logger = logging.getLogger(__name__)

async def verify_attachment_access(
    user_id: str,
    attachment_id: int,
    attachment_repository: Optional[AttachmentRepository] = None,
    course_repository: Optional[CourseRepository] = None
) -> Attachment:
    """
    첨부파일 접근 권한 검증
    
    Args:
        user_id: 접근을 요청하는 사용자 ID
        attachment_id: 접근하려는 첨부파일 ID
        attachment_repository: 첨부파일 저장소 (의존성 주입용)
        course_repository: 강의 저장소 (의존성 주입용)
        
    Returns:
        Attachment: 접근 권한이 있는 첨부파일 객체
        
    Raises:
        HTTPException: 파일을 찾을 수 없거나 접근 권한이 없는 경우
    """
    # 저장소 초기화 (의존성 주입이 없는 경우)
    if not attachment_repository:
        attachment_repository = AttachmentRepository()
    if not course_repository:
        course_repository = CourseRepository()
    
    # 첨부파일 조회
    attachment = await attachment_repository.get_by_id(attachment_id)
    if not attachment:
        logger.warning(f"첨부파일 접근 시도 실패: 존재하지 않는 파일 ID {attachment_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="첨부파일을 찾을 수 없습니다."
        )
    
    # 강의 접근 권한 확인
    course_id = attachment.course_id
    course = await course_repository.get_by_id(course_id)
    
    if not course:
        logger.warning(f"첨부파일 접근 시도 실패: 존재하지 않는 강의 ID {course_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="관련 강의를 찾을 수 없습니다."
        )
    
    # 사용자가 해당 강의에 접근 권한이 있는지 확인
    if course.user_id != user_id:
        logger.warning(f"첨부파일 접근 시도 실패: 사용자 {user_id}의 권한 없음")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 첨부파일에 접근할 권한이 없습니다."
        )
    
    return attachment

# 추가 보안 유틸리티 함수
async def verify_course_access(
    user_id: str,
    course_id: str,
    course_repository: Optional[CourseRepository] = None
) -> bool:
    """
    사용자의 강의 접근 권한 검증
    
    Args:
        user_id: 접근을 요청하는 사용자 ID
        course_id: 접근하려는 강의 ID
        db: 데이터베이스 세션
        course_repository: 강의 저장소 (의존성 주입용)
        
    Returns:
        bool: 접근 권한이 있으면 True
        
    Raises:
        HTTPException: 강의를 찾을 수 없거나 접근 권한이 없는 경우
    """
    # 저장소 초기화 (의존성 주입이 없는 경우)
    if not course_repository:
        course_repository = CourseRepository()
    
    # 강의 조회
    course = await course_repository.get_by_id(course_id)
    if not course:
        logger.warning(f"강의 접근 시도 실패: 존재하지 않는 강의 ID {course_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="강의를 찾을 수 없습니다."
        )
    
    # 사용자가 해당 강의에 접근 권한이 있는지 확인
    if course.user_id != user_id:
        logger.warning(f"강의 접근 시도 실패: 사용자 {user_id}의 권한 없음")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 강의에 접근할 권한이 없습니다."
        )
    
    return True

async def verify_content_access(
    user_id: str,
    content_id: int,
    course_id: str,
    content_type: str,
    db: AsyncSession,
    repository: Any = None,
    course_repository: Optional[CourseRepository] = None
) -> Any:
    """
    콘텐츠(공지사항, 강의자료, 과제 등) 접근 권한 검증
    
    Args:
        user_id: 접근을 요청하는 사용자 ID
        content_id: 접근하려는 콘텐츠 ID
        course_id: 접근하려는 강의 ID
        content_type: 콘텐츠 유형 ('notices', 'materials', 'assignments' 등)
        db: 데이터베이스 세션
        repository: 콘텐츠 저장소 (의존성 주입용)
        course_repository: 강의 저장소 (의존성 주입용)
        
    Returns:
        Any: 접근 권한이 있는 콘텐츠 객체
        
    Raises:
        HTTPException: 콘텐츠를 찾을 수 없거나 접근 권한이 없는 경우
    """
    # 강의 접근 권한 확인
    await verify_course_access(user_id, course_id, db, course_repository)
    
    # 콘텐츠 조회
    if repository:
        content = await repository.get_by_id(db, content_id)
        if not content:
            logger.warning(f"{content_type} 접근 시도 실패: 존재하지 않는 ID {content_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{content_type}을(를) 찾을 수 없습니다."
            )
        
        # 콘텐츠가 해당 강의에 속하는지 확인
        if getattr(content, 'course_id', None) != course_id:
            logger.warning(f"{content_type} 접근 시도 실패: 강의 불일치 (요청: {course_id}, 실제: {content.course_id})")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"해당 {content_type}은(는) 지정된 강의에 속하지 않습니다."
            )
        
        return content
    
    return None
