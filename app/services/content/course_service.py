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

    async def get_courses(self, user_id: str, blank_auto_fetch: bool = True) -> List[Dict[str, Any]]:
        """
        사용자의 강의 목록 조회 (필요시 자동 크롤링 포함)
        
        Args:
            user_id: 사용자 ID
            blank_auto_fetch: 빈 목록일 때 자동으로 초기 크롤링 수행 여부
            
        Returns:
            강의 목록 (필요시 새로 크롤링된 목록 포함)
        """
        try:
            logger.info(f"사용자 {user_id}의 강의 목록 조회 시작")
            existing_courses = await self.repository.get_by_user_id(user_id)
            
            # 빈 목록이고 auto_fetch가 활성화된 경우 초기 크롤링 수행
            if not existing_courses and blank_auto_fetch:
                logger.info(f"사용자 {user_id}의 강의 목록이 비어있음 - 초기 크롤링 시작")
                try:
                    fetched_courses = await self.refresh_courses(user_id)
                    if fetched_courses:
                        logger.info(f"초기 크롤링 완료: {len(fetched_courses)}개 강의 발견")
                        return fetched_courses
                    else:
                        logger.warning("초기 크롤링을 수행했으나 강의를 찾을 수 없음")
                except Exception as fetch_error:
                    logger.error(f"초기 크롤링 중 오류 발생: {str(fetch_error)}")
                    # 크롤링 실패시 빈 배열 반환
                
            logger.info(f"강의 목록 반환: {len(existing_courses)}개")
            return existing_courses
            
        except Exception as e:
            logger.error(f"강의 목록 조회 중 오류 발생: {str(e)}")
            return []

    async def refresh_courses(self, user_id: str) -> List[Dict[str, Any]]:
        """
        이클래스에서 강의 목록을 실시간으로 가져와서 데이터베이스에 동기화
        
        주요 기능:
        - 이클래스 로그인 및 강의 목록 페이지 크롤링
        - HTML 파싱을 통한 강의 정보 추출  
        - 데이터베이스에 강의 정보 저장/업데이트
        - 사용자-강의 등록 관계 설정
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            새로 가져온/업데이트된 강의 목록
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
                    logger.error(f"강의 저장 중 오류: {course_info.get('course_id', 'unknown')} - {str(save_error)}")
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
            course_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        특정 강의의 상세 정보 조회
        
        Args:
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
