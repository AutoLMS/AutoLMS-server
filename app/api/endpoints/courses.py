from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.course import Course, CourseList
from app.schemas.crawl import CrawlTaskResponse
from app.api.deps import get_current_user, get_db_session, get_eclass_service
from app.services.eclass_service import EclassService
from app.services.test_data_service import TestDataService
from app.core.config import settings

router = APIRouter()

# 개발 환경에서는 TestDataService 사용
def get_test_data_service():
    return TestDataService()

@router.get("/", response_model=CourseList)
async def get_courses(
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    eclass_service: EclassService = Depends(get_eclass_service),
    test_data_service: TestDataService = Depends(get_test_data_service)
) -> Any:
    """모든 강의 목록 조회"""

    # 개발 환경에서는 테스트 데이터 사용
    if settings.ENVIRONMENT == "development":
        courses = test_data_service.get_courses(current_user["id"])
        return {
            "courses": courses,
            "total": len(courses)
        }

    # 프로덕션 환경에서는 실제 eClass 서비스 사용
    try:
        # Supabase Auth 기반 사용자 (새로운 인증 시스템)
        print(f"🐛 DEBUG: Supabase Auth 사용자 - ID: {current_user['id']}")
        
        # AuthService를 통해 eClass 로그인 정보 가져오기
        from app.services.auth_service import AuthService
        auth_service = AuthService()
        
        try:
            eclass_credentials = await auth_service.get_user_eclass_credentials(current_user["id"])
            print(f"🐛 DEBUG: eClass 자격증명 조회 성공 - 사용자명: {eclass_credentials['eclass_username']}")
        except Exception as cred_error:
            print(f"🐛 DEBUG: 자격증명 조회 실패: {cred_error}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"사용자 자격증명 조회 실패: {str(cred_error)}"
            )
        
        try:
            login_success = await eclass_service.login(
                eclass_credentials["eclass_username"], 
                eclass_credentials["eclass_password"]
            )
            print(f"🐛 DEBUG: eClass 로그인 시도 결과: {login_success}")
        except Exception as login_error:
            print(f"🐛 DEBUG: eClass 로그인 시도 중 오류: {login_error}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"eClass 로그인 시도 중 오류: {str(login_error)}"
            )
        
        if not login_success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="e-Class 로그인에 실패했습니다."
            )
    except HTTPException:
        # HTTPException은 그대로 재발생
        raise
    except Exception as e:
        print(f"🐛 DEBUG: 예상치 못한 오류: {e}")
        import traceback
        print(f"🐛 DEBUG: 트레이스백: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"예상치 못한 오류 발생: {str(e)}"
        )
    
    courses = await eclass_service.get_courses(current_user["id"], force_refresh=True, is_jwt_user=True)
    return {
        "courses": courses,
        "total": len(courses)
    }

@router.get("/crawl", response_model=CrawlTaskResponse)
async def crawl_all_courses(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user),
    eclass_service: EclassService = Depends(get_eclass_service),
    auto_download: bool = False
) -> Any:
    """모든 강의 자료 크롤링"""
    # e-Class 로그인 확인
    if not await eclass_service.is_logged_in():
        try:
            # AuthService를 통해 eClass 로그인 정보 가져오기
            from app.services.auth_service import AuthService
            auth_service = AuthService()
            eclass_credentials = await auth_service.get_user_eclass_credentials(current_user["id"])
            
            login_success = await eclass_service.login(
                eclass_credentials["eclass_username"], 
                eclass_credentials["eclass_password"]
            )
            if not login_success:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="e-Class 로그인에 실패했습니다."
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"e-Class 로그인 중 오류가 발생했습니다: {str(e)}"
            )

    return await eclass_service.crawl_all_courses(current_user["id"], auto_download, is_jwt_user=True)

@router.get("/{course_id}", response_model=Course)
async def get_course(
    course_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user),
    eclass_service: EclassService = Depends(get_eclass_service),
    test_data_service: TestDataService = Depends(get_test_data_service)
) -> Any:
    """특정 강의 정보 조회"""

    # 개발 환경에서는 테스트 데이터 사용
    if settings.ENVIRONMENT == "development":
        course = test_data_service.get_course_by_id(current_user["id"], course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="강의를 찾을 수 없습니다"
            )
        return course

    # 프로덕션 환경에서는 실제 eClass 서비스 사용
    if not await eclass_service.is_logged_in():
        try:
            # AuthService를 통해 eClass 로그인 정보 가져오기
            from app.services.auth_service import AuthService
            auth_service = AuthService()
            eclass_credentials = await auth_service.get_user_eclass_credentials(current_user["id"])
            
            login_success = await eclass_service.login(
                eclass_credentials["eclass_username"], 
                eclass_credentials["eclass_password"]
            )
            if not login_success:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="e-Class 로그인에 실패했습니다."
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"e-Class 로그인 중 오류가 발생했습니다: {str(e)}"
            )

    courses = await eclass_service.get_courses(current_user["id"], is_jwt_user=True)
    for course in courses:
        if course and course.get('id') == course_id:
            return course

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="강의를 찾을 수 없습니다"
    )

@router.post("/refresh", response_model=CourseList)
async def refresh_courses(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
    current_user: dict = Depends(get_current_user),
    eclass_service: EclassService = Depends(get_eclass_service),
    test_data_service: TestDataService = Depends(get_test_data_service)
) -> Any:
    """강의 목록 새로고침 (e-Class에서 다시 가져오기)"""

    # 개발 환경에서는 테스트 데이터 사용
    if settings.ENVIRONMENT == "development":
        courses = test_data_service.get_courses(current_user["id"])
        return {
            "courses": courses,
            "total": len(courses),
            "message": "강의 목록 새로고침이 완료되었습니다"
        }

    # 프로덕션 환경에서는 실제 eClass 서비스 사용    
    if not await eclass_service.is_logged_in():
        try:
            # AuthService를 통해 eClass 로그인 정보 가져오기
            from app.services.auth_service import AuthService
            auth_service = AuthService()
            eclass_credentials = await auth_service.get_user_eclass_credentials(current_user["id"])
            
            login_success = await eclass_service.login(
                eclass_credentials["eclass_username"], 
                eclass_credentials["eclass_password"]
            )
            if not login_success:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="e-Class 로그인에 실패했습니다."
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"e-Class 로그인 중 오류가 발생했습니다: {str(e)}"
            )

    # 강제 새로고침
    courses = await eclass_service.get_courses(current_user["id"], force_refresh=True, is_jwt_user=True)

    return {
        "courses": courses,
        "total": len(courses),
        "message": "강의 목록 새로고침이 완료되었습니다"
    }
