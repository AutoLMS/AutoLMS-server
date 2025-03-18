import logging
import asyncio
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Set

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.eclass_session import EclassSession
from app.services.eclass_parser import EclassParser
from app.services.file_handler import FileHandler
from app.db.repositories.course_repository import CourseRepository
from app.db.repositories.material_repository import MaterialRepository

logger = logging.getLogger(__name__)

class EclassService:
    """통합 e-Class 서비스"""

    def __init__(self, session=None, parser=None, file_handler=None):
        """EclassService 초기화"""
        self.session = session or EclassSession()
        self.parser = parser or EclassParser()
        self.file_handler = file_handler or FileHandler()

    async def login(self, username: str, password: str) -> bool:
        """e-Class 로그인"""
        return await self.session.login(username, password)

    async def is_logged_in(self) -> bool:
        """로그인 상태 확인"""
        return await self.session.is_logged_in()

    async def get_courses(self, user_id: str, db: AsyncSession, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        강의 목록 조회 및 DB 동기화

        Args:
            user_id: 사용자 ID
            db: 데이터베이스 세션
            force_refresh: 강제 새로고침 여부

        Returns:
            List[Dict[str, Any]]: 강의 목록
        """
        logger.info(f"사용자 {user_id}의 강의 목록 조회 시작")

        # 로그인 상태 확인
        if not await self.is_logged_in():
            logger.error("로그인되지 않은 상태에서 강의 목록 조회 시도")
            return []

        # 이미 저장된 강의 목록 가져오기
        course_repo = CourseRepository()
        existing_courses = await course_repo.get_by_user_id(db, user_id)

        # 강제 새로고침이 아니고 저장된 강의가 있으면 그대로 반환
        if not force_refresh and existing_courses:
            logger.info(f"저장된 강의 목록 반환: {len(existing_courses)}개")
            return existing_courses  # Course 모델이 dict로 변환되도록 수정 필요

        # e-Class에서 강의 목록 가져오기
        html = await self.session.get_course_list()
        if not html:
            logger.error("강의 목록을 가져오는데 실패했습니다")
            return []
            
        courses = self.parser.parse_courses(html)
        if not courses:
            logger.warning("e-Class에서 가져온 강의 목록이 비어 있습니다")
            return []

        # 데이터베이스에 강의 정보 저장
        existing_course_ids = {course.id for course in existing_courses}
        updated_courses = []

        for course in courses:
            course_dict = {
                'id': course.get('id'),  # course_id 대신 id 사용
                'user_id': user_id,
                'name': course.get('name', ''),
                'code': course.get('code', ''),
                'time': course.get('time', ''),
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }

            try:
                if course['id'] in existing_course_ids:
                    # 기존 강의 업데이트
                    existing_course = next(c for c in existing_courses if c.id == course['id'])
                    updated_course = await course_repo.update(db, existing_course, **course_dict)
                    updated_courses.append(updated_course)
                else:
                    # 새 강의 추가
                    new_course = await course_repo.create(db, **course_dict)
                    updated_courses.append(new_course)
            except Exception as e:
                logger.error(f"강의 정보 저장 중 오류 발생: {str(e)}")
                continue

        logger.info(f"강의 목록 동기화 완료: {len(updated_courses)}개")
        return updated_courses