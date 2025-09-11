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

    async def get_courses(self, user_id: str) -> List[Dict[str, Any]]:
        """
        데이터베이스에서 사용자의 기존 강의 목록 조회 (단순 조회만 담당)
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            기존에 저장된 강의 목록
        """
        try:
            logger.info(f"사용자 {user_id}의 기존 강의 목록 조회")
            existing_courses = await self.repository.get_by_user_id(user_id)
            logger.info(f"기존 강의 목록 반환: {len(existing_courses)}개")
            return existing_courses
        except Exception as e:
            logger.error(f"강의 목록 조회 중 오류 발생: {str(e)}")
            return []

    async def refresh_courses(self, user_id: str) -> List[Dict[str, Any]]:
        """
        이클래스에서 새 강의 목록을 가져와 파싱하고 저장 (크롤링/파싱/저장 담당)
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            새로 가져온 강의 목록
        """
        try:
            logger.info(f"사용자 {user_id}의 강의 목록 새로고침 시작")

            # 1. EclassSession 객체 가져오기
            eclass_session = await self.session_service.get_session(user_id)
            if not eclass_session:
                logger.error("이클래스 세션을 가져올 수 없음")
                return []
            
            # 2. EclassSession의 get_course_list 메서드 사용
            html = await eclass_session.get_course_list()
            if not html:
                logger.error("강의 목록을 가져오는데 실패했습니다")
                return []

            # 3. HTML 파싱
            courses_data = self.parser.parse_list(html)
            if not courses_data:
                logger.warning("e-Class에서 가져온 강의 목록이 비어 있습니다")
                return []

            logger.info(f"e-Class에서 {len(courses_data)}개의 강의를 파싱했습니다")

            # 4. 데이터베이스에 저장
            saved_courses = []
            for course_info in courses_data:
                try:
                    # 강의 저장 및 사용자 등록
                    saved_course = await self.repository.upsert_with_user_enrollment(
                        user_id=user_id,
                        **course_info
                    )
                    if saved_course:
                        saved_courses.append(saved_course)
                        
                except Exception as save_error:
                    logger.error(f"강의 저장 중 오류: {course_info.get('id', 'unknown')} - {str(save_error)}")
                    continue

            logger.info(f"총 {len(saved_courses)}개의 강의가 저장되었습니다")
            return saved_courses

        except Exception as e:
            logger.error(f"강의 목록 새로고침 중 오류 발생: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    async def get_course(
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
