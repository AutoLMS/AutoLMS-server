import asyncio
import logging
from fastapi import FastAPI

from app.api.deps import (
    get_session_service, 
    get_storage_service,
    get_course_service,
    get_notice_service,
    get_material_service,
    get_assignment_service,
    get_syllabus_service,
    get_crawl_service
)

logger = logging.getLogger(__name__)

async def startup_event(app: FastAPI) -> None:
    """애플리케이션 시작 시 실행할 이벤트"""
    logger.info("애플리케이션 시작 이벤트 실행")
    
    # 세션 서비스 초기화
    session_service = get_session_service()
    await session_service.initialize()
    
    # 스토리지 서비스 초기화
    storage_service = get_storage_service()
    await storage_service.initialize()
    
    # 콘텐츠 서비스 초기화
    course_service = get_course_service()
    await course_service.initialize()
    
    notice_service = get_notice_service()
    await notice_service.initialize()
    
    material_service = get_material_service()
    await material_service.initialize()
    
    assignment_service = get_assignment_service()
    await assignment_service.initialize()
    
    syllabus_service = get_syllabus_service()
    await syllabus_service.initialize()
    
    # 크롤링 서비스 초기화
    crawl_service = get_crawl_service()
    await crawl_service.initialize()
    
    # 세션 체크 백그라운드 작업 시작
    asyncio.create_task(session_check_task())
    
    logger.info("모든 서비스 초기화 완료")

async def shutdown_event(app: FastAPI) -> None:
    """애플리케이션 종료 시 실행할 이벤트"""
    logger.info("애플리케이션 종료 이벤트 실행")
    
    # 크롤링 서비스 종료
    crawl_service = get_crawl_service()
    await crawl_service.close()
    
    # 콘텐츠 서비스 종료
    syllabus_service = get_syllabus_service()
    await syllabus_service.close()
    
    assignment_service = get_assignment_service()
    await assignment_service.close()
    
    material_service = get_material_service()
    await material_service.close()
    
    notice_service = get_notice_service()
    await notice_service.close()
    
    course_service = get_course_service()
    await course_service.close()
    
    # 스토리지 서비스 종료
    storage_service = get_storage_service()
    await storage_service.close()
    
    # 세션 서비스 종료 (마지막에 종료)
    session_service = get_session_service()
    await session_service.close()
    
    logger.info("모든 서비스 종료 완료")

async def session_check_task() -> None:
    """세션 건강 상태 주기적 확인 태스크"""
    session_service = get_session_service()
    
    while True:
        try:
            await asyncio.sleep(600)  # 10분마다
            await session_service.check_sessions_health()
        except asyncio.CancelledError:
            logger.info("세션 체크 태스크 취소됨")
            break
        except Exception as e:
            logger.error(f"세션 체크 중 오류 발생: {str(e)}")

def register_startup_and_shutdown_events(app: FastAPI) -> None:
    """애플리케이션에 시작 및 종료 이벤트 등록"""
    app.add_event_handler("startup", lambda: startup_event(app))
    app.add_event_handler("shutdown", lambda: shutdown_event(app))
