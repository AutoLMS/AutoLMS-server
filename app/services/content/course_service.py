import logging
from typing import List, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.base_service import BaseService
from app.services.session import EclassSessionManager
from app.services.parsers.course_parser import CourseParser
from app.db.repositories.course_repository import CourseRepository
from app.models.course import Course

logger = logging.getLogger(__name__)


class CourseService(BaseService):
    """강의 관련 서비스"""

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
            db: AsyncSession,
            force_refresh: bool = False
    ) -> List[Course]:
        """
        사용자의 강의 목록 조회

        Args:
            user_id: 사용자 ID
            db: 데이터베이스 세션
            force_refresh: 강제 새로고침 여부

        Returns:
            List[Course]: 강의 목록
        """
        logger.info(f"사용자 {user_id}의 강의 목록 조회 시작")

        # 이미 저장된 강의 목록 가져오기
        if not force_refresh:
            existing_courses = await self.repository.get_by_user_id(db, user_id)
            if existing_courses:
                logger.info(f"저장된 강의 목록 반환: {len(existing_courses)}개")
                return existing_courses

        # e-Class에서 강의 목록 가져오기
        eclass_session = await self.session_service.get_session(user_id)
        if not eclass_session:
            logger.error("이클래스 세션을 가져올 수 없음")
            return []

        html = await eclass_session.get_course_list()
        if not html:
            logger.error("강의 목록을 가져오는데 실패했습니다")
            return []

        courses_data = self.parser.parse_list(html)
        if not courses_data:
            logger.warning("e-Class에서 가져온 강의 목록이 비어 있습니다")
            return []

        # 기존 강의 목록 조회
        existing_courses = await self.repository.get_by_user_id(db, user_id)
        existing_course_ids = {course.id for course in existing_courses}

        # 데이터베이스에 강의 정보 저장
        updated_courses = []

        for course_data in courses_data:
            try:
                course_dict = {
                    'id': course_data.get('id'),
                    'user_id': user_id,
                    'name': course_data.get('name', ''),
                    'code': course_data.get('code', ''),
                    'time': course_data.get('time', ''),
                }

                if course_data['id'] in existing_course_ids:
                    # 기존 강의 업데이트
                    existing_course = next(c for c in existing_courses if c.id == course_data['id'])
                    updated_course = await self.repository.update(
                        db,
                        existing_course.id,
                        course_dict
                    )
                else:
                    # 새 강의 추가
                    updated_course = await self.repository.create(db, course_dict)

                updated_courses.append(updated_course)

            except Exception as e:
                logger.error(f"강의 정보 저장 중 오류 발생: {str(e)}")
                continue

        logger.info(f"강의 목록 동기화 완료: {len(updated_courses)}개")
        return updated_courses

    async def get_course(self, user_id: str, course_id: str, db: AsyncSession) -> Optional[Course]:
        """
        특정 강의 조회

        Args:
            user_id: 사용자 ID
            course_id: 강의 ID
            db: 데이터베이스 세션

        Returns:
            Optional[Course]: 강의 정보
        """
        logger.info(f"사용자 {user_id}의 강의 {course_id} 조회")

        # 강의 정보 조회
        course = await self.repository.get_by_id(db, course_id)

        # 사용자 확인
        if course and course.user_id == user_id:
            return course

        return None

    async def get_course_menus(self, user_id: str, course_id: str) -> Dict[str, Dict[str, Any]]:
        """
        강의 메뉴 목록 조회

        Args:
            user_id: 사용자 ID
            course_id: 강의 ID

        Returns:
            Dict[str, Dict[str, Any]]: 메뉴 정보
        """
        logger.info(f"사용자 {user_id}의 강의 {course_id} 메뉴 조회")

        # e-Class 세션 가져오기
        eclass_session = await self.session_service.get_session(user_id)
        if not eclass_session:
            logger.error("이클래스 세션을 가져올 수 없음")
            return {}

        # 강의실 접근
        course_url = await eclass_session.access_course(course_id)
        if not course_url:
            logger.error(f"강의실 접근 실패: {course_id}")
            return {}

        # 강의 메뉴 가져오기
        response = await eclass_session.get(course_url)
        if not response:
            logger.error(f"강의실 페이지 요청 실패: {course_id}")
            return {}

        course_menus = self.parser.parse_course_menus(response.text)
        logger.info(f"강의 {course_id}의 메뉴 파싱 완료: {len(course_menus)}개")

        return course_menus