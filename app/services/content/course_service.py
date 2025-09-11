import logging
from typing import List, Dict, Any, Optional

from app.services.base_service import BaseService
from app.services.session import EclassSessionManager
from app.services.parsers.course_parser import CourseParser
from app.db.repositories.course_repository import CourseRepository

logger = logging.getLogger(__name__)


class CourseService(BaseService):
    """강의 관리 서비스"""
    
    def __init__(
            self,
            session_service: EclassSessionManager,
            course_parser: CourseParser,
            course_repository: CourseRepository
    ):
        self.session_service = session_service
        self.parser = course_parser
        self.repository = course_repository
        logger.info("CourseService 초기화 완료")

    async def initialize(self) -> None:
        """서비스 초기화"""
        logger.info("CourseService 시작")
        pass

    async def close(self) -> None:
        """서비스 리소스 정리"""
        logger.info("CourseService 종료")
        pass

    async def get_courses(
            self,
            user_id: str,
            force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        사용자의 강의 목록 조회
        
        Args:
            user_id: 사용자 ID
            force_refresh: 강제 새로고침 여부
            
        Returns:
            강의 목록
        """
        try:
            logger.info(f"사용자 {user_id}의 강의 목록 조회 시작")
            
            if not force_refresh:
                # 기존 저장된 강의 목록 조회
                existing_courses = await self.repository.get_by_user_id(user_id)
                if existing_courses:
                    logger.info(f"기존 강의 목록 반환: {len(existing_courses)}개")
                    return existing_courses
            
            # e-Class에서 새로 가져오기
            html = await self.session_service.get_courses_html(user_id)
            if not html:
                logger.error("강의 목록을 가져오는데 실패했습니다")
                return []

            courses_data = self.parser.parse_list(html)

            if not courses_data:
                logger.warning("e-Class에서 가져온 강의 목록이 비어 있습니다")
                return []

            logger.info(f"e-Class에서 {len(courses_data)}개의 강의를 파싱했습니다")

            # Supabase에 저장
            saved_courses = []
            for course_info in courses_data:
                try:
                    # 강의 저장
                    saved_course = await self.repository.save_course(
                        user_id=user_id,
                        course_data=course_info
                    )
                    if saved_course:
                        saved_courses.append(saved_course)
                        
                except Exception as save_error:
                    logger.error(f"강의 저장 중 오류: {course_info.get('id', 'unknown')} - {str(save_error)}")
                    continue

            logger.info(f"총 {len(saved_courses)}개의 강의가 저장되었습니다")
            return saved_courses

        except Exception as e:
            logger.error(f"강의 목록 조회 중 오류 발생: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    async def get_course_detail(
            self,
            user_id: str,
            course_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        특정 강의의 상세 정보 조회
        
        Args:
            user_id: 사용자 ID
            course_id: 강의 ID
            
        Returns:
            강의 상세 정보
        """
        try:
            course = await self.repository.get_by_course_id(course_id)
            if course:
                logger.info(f"강의 상세 정보 조회 성공: {course_id}")
                return course
            else:
                logger.warning(f"강의를 찾을 수 없음: {course_id}")
                return None
                
        except Exception as e:
            logger.error(f"강의 상세 정보 조회 중 오류: {str(e)}")
            return None

    async def refresh_course_list(self, user_id: str) -> List[Dict[str, Any]]:
        """
        강의 목록 강제 새로고침
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            새로 가져온 강의 목록
        """
        logger.info(f"사용자 {user_id}의 강의 목록 강제 새로고침")
        return await self.get_courses(user_id, force_refresh=True)

    async def search_courses(
            self,
            user_id: str,
            keyword: str
    ) -> List[Dict[str, Any]]:
        """
        강의 검색
        
        Args:
            user_id: 사용자 ID
            keyword: 검색 키워드
            
        Returns:
            검색된 강의 목록
        """
        try:
            all_courses = await self.get_courses(user_id)
            
            # 간단한 키워드 검색
            filtered_courses = []
            for course in all_courses:
                course_name = course.get('course_name', '').lower()
                instructor = course.get('instructor', '').lower()
                keyword_lower = keyword.lower()
                
                if keyword_lower in course_name or keyword_lower in instructor:
                    filtered_courses.append(course)
            
            logger.info(f"키워드 '{keyword}'로 {len(filtered_courses)}개 강의 검색됨")
            return filtered_courses
            
        except Exception as e:
            logger.error(f"강의 검색 중 오류: {str(e)}")
            return []