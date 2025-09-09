import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import select, insert, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.services.base_service import BaseService
from app.services.session import EclassSessionManager
from app.services.parsers.course_parser import CourseParser
from app.db.repositories.course_repository import CourseRepository
from app.models.course import Course
from app.models.user_courses import user_courses

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
        
        # 사용자 존재 여부 확인
        user_exists = await self._check_user_exists(db, user_id)
        if not user_exists:
            logger.error(f"사용자 ID {user_id}가 데이터베이스에 존재하지 않습니다")
            return []

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

        # HTML 내용 로깅 (디버깅용, 실제 환경에서는 제거)
        logger.debug(f"HTML 내용: {html[:500]}...")  # 첫 500자만 로깅

        courses_data = self.parser.parse_list(html)
        logger.debug(f"파싱된 강의 목록: {courses_data}")

        if not courses_data:
            logger.warning("e-Class에서 가져온 강의 목록이 비어 있습니다")
            return []

        # 기존 강의 목록 조회
        existing_courses = await self.repository.get_by_user_id(db, user_id)
        existing_course_ids = {course.id for course in existing_courses}
        
        # 모든 강의 목록 조회 (사용자에 관계없이)
        all_courses_query = select(Course)
        result = await db.execute(all_courses_query)
        all_courses = result.scalars().all()
        all_course_ids = {course.id for course in all_courses}

        # 데이터베이스에 강의 정보 저장
        updated_courses = []

        for course_data in courses_data:
            course_id = course_data.get('id')
            
            # 트랜잭션 격리를 위한 새 세션 시작
            try:
                course_dict = {
                    'id': course_id,
                    'name': course_data.get('name', ''),
                    'code': course_data.get('code', ''),
                    'semester': course_data.get('semester', ''),
                }

                # 강의가 데이터베이스에 이미 존재하는지 확인
                if course_id in all_course_ids:
                    # 기존 강의 찾기
                    course = next((c for c in all_courses if c.id == course_id), None)
                    if course:
                        updated_course = await self.repository.update(
                            db,
                            course,
                            **course_dict
                        )
                    else:
                        # 여기까지 오면 안되지만, 안전을 위해 추가
                        logger.warning(f"강의 ID {course_id}가 all_course_ids에 있지만 all_courses에서 찾을 수 없음")
                        course_query = select(Course).where(Course.id == course_id)
                        result = await db.execute(course_query)
                        course = result.scalar_one_or_none()
                        if course:
                            updated_course = await self.repository.update(
                                db,
                                course,
                                **course_dict
                            )
                        else:
                            logger.error(f"강의 ID {course_id}를 찾을 수 없음 - 데이터 불일치")
                            continue
                else:
                    # 새 강의 추가
                    try:
                        updated_course = await self.repository.create(
                            db,
                            **course_dict
                        )
                    except IntegrityError as e:
                        # 동시성 문제로 이미 다른 세션에서 삽입된 경우
                        logger.warning(f"강의 {course_id} 추가 중 무결성 오류 발생, 업데이트로 시도: {str(e)}")
                        await db.rollback()  # 세션 롤백
                        
                        # 강의 다시 조회
                        course_query = select(Course).where(Course.id == course_id)
                        result = await db.execute(course_query)
                        course = result.scalar_one_or_none()
                        
                        if course:
                            updated_course = await self.repository.update(
                                db,
                                course,
                                **course_dict
                            )
                        else:
                            logger.error(f"무결성 오류 후 강의 {course_id}를 찾을 수 없음")
                            continue

                # 사용자와 강의 연결 관계 처리
                if course_id not in existing_course_ids:
                    try:
                        # 이미 관계가 있는지 확인
                        relation_exists_query = select(exists().where(
                            (user_courses.c.user_id == user_id) & 
                            (user_courses.c.course_id == course_id)
                        ))
                        result = await db.execute(relation_exists_query)
                        relation_exists = result.scalar()
                        
                        if not relation_exists:
                            # user_courses 테이블에 관계 추가
                            stmt = insert(user_courses).values(
                                user_id=user_id,
                                course_id=updated_course.id,
                                semester=course_data.get('semester', ''),
                                time=course_data.get('time', '')
                            )
                            await db.execute(stmt)
                            await db.commit()
                    except IntegrityError as e:
                        logger.warning(f"사용자-강의 관계 추가 중 무결성 오류 발생: {str(e)}")
                        await db.rollback()
                        # 이미 관계가 존재하는 경우는 무시

                # 업데이트된 강의가 세션에 연결되어 있는지 확인
                if db.is_active and not db.in_transaction():
                    # 트랜잭션이 없는 경우 새 트랜잭션 시작
                    await db.begin()
                
                # course 객체를 항상 세션에 연결되도록 유지
                if updated_course not in db:
                    refreshed_query = select(Course).where(Course.id == updated_course.id)
                    refreshed_result = await db.execute(refreshed_query)
                    updated_course = refreshed_result.scalar_one_or_none()
                    if not updated_course:
                        logger.warning(f"강의 {course_id}를 세션에서 새로고침할 수 없음")
                        continue

                updated_courses.append(updated_course)

            except Exception as e:
                logger.error(f"강의 정보 저장 중 오류 발생: {str(e)}")
                if db.in_transaction():
                    await db.rollback()  # 오류 발생 시 롤백
                continue

        logger.info(f"강의 목록 동기화 완료: {len(updated_courses)}개")
        
        # 객체들이 여전히 세션에 연결되어 있도록 다시 조회
        try:
            if updated_courses:
                course_ids = [course.id for course in updated_courses]
                query = select(Course).where(Course.id.in_(course_ids))
                result = await db.execute(query)
                fresh_courses = result.scalars().all()
                return fresh_courses
            return []
        except Exception as e:
            logger.error(f"강의 목록 새로고침 중 오류 발생: {str(e)}")
            return updated_courses  # 원래 목록 반환 (부분적으로 동작할 수 있음)

    async def _check_user_exists(self, db: AsyncSession, user_id: str) -> bool:
        """
        사용자가 존재하는지 확인
        
        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            
        Returns:
            bool: 사용자 존재 여부
        """
        try:
            query = select(exists().where(User.id == user_id))
            result = await db.execute(query)
            return result.scalar()
        except Exception as e:
            logger.error(f"사용자 확인 중 오류 발생: {str(e)}")
            return False

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
        course = await self.repository.get_by_course_id(db, course_id)
        
        if not course:
            return None
            
        # 사용자 접근 권한 확인 (user_courses 테이블을 통해)
        query = select(exists().where(
            (user_courses.c.user_id == user_id) & 
            (user_courses.c.course_id == course_id)
        ))
        result = await db.execute(query)
        if result.scalar():
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