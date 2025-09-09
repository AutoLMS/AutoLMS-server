from fastapi import APIRouter
from app.api.endpoints import auth, courses, notices, materials, assignments, attachments, crawl, syllabus
from datetime import datetime

api_router = APIRouter()

# Health check 엔드포인트
@api_router.get("/health", tags=["시스템"])
async def health_check():
    """시스템 상태 확인"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "AutoLMS API",
        "version": "1.0.0"
    }

# 인증 관련 엔드포인트
api_router.include_router(auth.router, prefix="/auth", tags=["인증"])

# 강의 관련 엔드포인트
api_router.include_router(courses.router, prefix="/courses", tags=["강의"])
api_router.include_router(notices.router, prefix="/courses/{course_id}/notices", tags=["공지사항"])
api_router.include_router(materials.router, prefix="/courses/{course_id}/materials", tags=["강의자료"])
api_router.include_router(assignments.router, prefix="/courses/{course_id}/assignments", tags=["과제"])

# 크롤링 관련 엔드포인트
api_router.include_router(crawl.router, prefix="/crawl", tags=["크롤링"])

# 첨부파일 관련 엔드포인트
api_router.include_router(attachments.router, prefix="/attachments", tags=["첨부파일"])

# 강의계획서 관련 엔드포인트
api_router.include_router(syllabus.router, prefix="/courses/{course_id}/syllabus", tags=["강의계획서"])