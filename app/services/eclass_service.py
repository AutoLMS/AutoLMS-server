import logging
import asyncio
import uuid
from datetime import datetime
from typing import List, Dict, Any
import os

from app.db.repositories import NoticeRepository, AttachmentRepository, AssignmentRepository
from app.services.eclass_session import EclassSession
from app.services.eclass_parser import EclassParser
from app.services.file_handler import FileHandler
from app.db.repositories.course_repository import CourseRepository
from app.db.repositories.material_repository import MaterialRepository

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.attachment import Attachment
from fastapi import HTTPException


logger = logging.getLogger(__name__)

class EclassService:
    """통합 e-Class 서비스"""

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, session=None, parser=None, file_handler=None):
        if not self._initialized:
            self.session = session or EclassSession()
            self.parser = parser or EclassParser()
            self.file_handler = file_handler or FileHandler()
            self.active_tasks = {}  # active_tasks 초기화 추가
            self._initialized = True

    async def login(self, username: str, password: str) -> bool:
        """e-Class 로그인"""
        return await self.session.login(username, password)

    async def is_logged_in(self) -> bool:
        """로그인 상태 확인"""
        return await self.session.is_logged_in()

    async def ensure_logged_in(self) -> bool:
        """로그인 상태 보장"""
        if await self.is_logged_in():
            return True

        from app.core.config import settings
        return await self.login(settings.ECLASS_USERNAME, settings.ECLASS_PASSWORD)

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
                'id': course.get('id'),
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


    async def crawl_course(self, user_id: str, course_id: str, db_session, auto_download: bool = False) -> Dict[
        str, Any]:
        """
        특정 강의 크롤링 작업 시작

        Args:
            user_id: 사용자 ID
            course_id: 강의 ID
            db_session: 데이터베이스 세션
            auto_download: 첨부파일 자동 다운로드 여부

        Returns:
            Dict[str, Any]: 크롤링 작업 정보
        """
        # 작업 ID 생성
        task_id = f"crawl_{course_id}_{uuid.uuid4().hex[:8]}"

        logger.info(f"강의 크롤링 작업 시작: {task_id} (강의: {course_id}, 사용자: {user_id})")

        # 로그인 상태 확인 및 자동 로그인 시도
        if not await self.ensure_logged_in():
            logger.error("e-Class 로그인 실패")
            return {
                "task_id": task_id,
                "status": "error",
                "message": "e-Class 로그인 실패",
                "course_id": course_id
            }

        # 작업 시작
        task = asyncio.create_task(
            self._crawl_course_task(user_id, course_id, db_session, auto_download, task_id)
        )

        # 작업 관리
        self.active_tasks[task_id] = {
            "task": task,
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "course_id": course_id,
            "user_id": user_id,
            "auto_download": auto_download
        }

        return {
            "task_id": task_id,
            "status": "running",
            "message": "크롤링 작업이 시작되었습니다",
            "course_id": course_id
        }

    async def _crawl_course_task(self, user_id: str, course_id: str, db_session, auto_download: bool, task_id: str) -> \
            Dict[str, Any]:
        """
        강의 크롤링 작업 수행

        Args:
            user_id: 사용자 ID
            course_id: 강의 ID
            db_session: 데이터베이스 세션
            auto_download: 첨부파일 자동 다운로드 여부
            task_id: 작업 ID

        Returns:
            Dict[str, Any]: 크롤링 결과
        """
        try:
            # 작업 상태 업데이트
            if task_id not in self.active_tasks:
                self.active_tasks[task_id] = {
                    "status": "running",
                    "start_time": datetime.now().isoformat(),
                }

            self.active_tasks[task_id]["status"] = "processing"

            # 크롤링 결과 저장
            result = {
                "task_id": task_id,
                "course_id": course_id,
                "user_id": user_id,
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "details": {
                    "notices": {"count": 0, "new": 0, "errors": 0},
                    "materials": {"count": 0, "new": 0, "errors": 0},
                    "assignments": {"count": 0, "new": 0, "errors": 0},
                    "attachments": {"count": 0, "success": 0, "errors": 0}
                }
            }

            # 강의실 접근
            course_url = await self.session.access_course(course_id)
            if not course_url:
                logger.error(f"강의실 접근 실패: {course_id}")
                result["status"] = "error"
                result["message"] = "강의실 접근 실패"
                return result

            # 강의 메뉴 확인
            response = await self.session.get(course_url)
            course_menus = self.parser.parse_course_menus(response.text)

            # 공지사항 크롤링
            if "notice" in course_menus:
                notice_result = await self._crawl_notices(
                    user_id, course_id, course_menus["notice"]["url"], db_session, auto_download
                )
                result["details"]["notices"] = notice_result

            # 강의자료 크롤링
            if "lecture_material" in course_menus:
                material_result = await self._crawl_materials(
                    user_id, course_id, course_menus["lecture_material"]["url"], db_session, auto_download
                )
                result["details"]["materials"] = material_result

            # 과제 크롤링
            if "assignment" in course_menus:
                assignment_result = await self._crawl_assignments(
                    user_id, course_id, course_menus["assignment"]["url"], db_session, auto_download
                )
                result["details"]["assignments"] = assignment_result

            # 작업 완료
            if task_id in self.active_tasks:
                self.active_tasks[task_id]["status"] = "completed"
                self.active_tasks[task_id]["end_time"] = datetime.now().isoformat()
                self.active_tasks[task_id]["result"] = result

            logger.info(f"강의 크롤링 작업 완료: {task_id}")
            return result

        except Exception as e:
            logger.exception(f"강의 크롤링 작업 중 오류 발생: {e}")

            # 작업 실패
            if task_id in self.active_tasks:
                self.active_tasks[task_id]["status"] = "failed"
                self.active_tasks[task_id]["error"] = str(e)
                self.active_tasks[task_id]["end_time"] = datetime.now().isoformat()

            return {
                "task_id": task_id,
                "course_id": course_id,
                "user_id": user_id,
                "status": "error",
                "message": f"크롤링 중 오류 발생: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    async def _crawl_notices(self, user_id: str, course_id: str, notice_url: str, db_session, auto_download: bool) -> \
    Dict[str, Any]:
        """공지사항 크롤링"""
        result = {"count": 0, "new": 0, "errors": 0}

        try:
            # 1. 공지사항 목록 페이지 접근
            base_url = "https://eclass.seoultech.ac.kr"
            notice_url = f"{base_url}{notice_url}" if not notice_url.startswith("http") else notice_url
            notice_url = notice_url.replace('notice_list_form', 'notice_list')

            # 2. 목록 데이터 요청 (material과 유사한 방식으로 변경)
            data = {
                'start': '1',
                'display': '100',  # 한 번에 가져올 개수 증가
                'SCH_VALUE': '',
                'ud': self.session.user_id,
                'ky': course_id,
                'encoding': 'utf-8'
            }

            response = await self.session.post(notice_url, data=data)
            if not response:
                logger.error("공지사항 목록 요청 실패")
                return result

            # 3. 목록 파싱
            notices = self.parser.parse_notice_list(response.text)
            if not notices:
                logger.info(f"강의 {course_id}의 공지사항이 없습니다.")
                return result

            # 4. 기존 공지사항 조회
            notice_repo = NoticeRepository()
            attachment_repo = AttachmentRepository()
            existing_notices = await notice_repo.get_by_course_id(db_session, course_id)
            existing_article_ids = {notice.article_id for notice in existing_notices}

            # 5. 각 공지사항 처리
            for notice in notices:
                result["count"] += 1
                article_id = notice.get("article_id")

                if not article_id:
                    result["errors"] += 1
                    continue

                try:
                    # 이미 존재하는 공지사항 건너뛰기
                    if article_id in existing_article_ids:
                        continue

                    # 상세 페이지 요청 (material과 유사하게 처리)
                    detail_url = notice.get("url")
                    detail_response = await self.session.get(detail_url)
                    if not detail_response:
                        logger.error(f"공지사항 상세 정보 요청 실패: {article_id}")
                        result["errors"] += 1
                        continue

                    # 상세 정보 파싱
                    notice_detail = self.parser.parse_notice_detail(detail_response.text)
                    notice.update(notice_detail)

                    # DB 저장
                    notice_data = {
                        'article_id': article_id,
                        'course_id': course_id,
                        'title': notice.get('title'),
                        'content': notice_detail.get('content'),
                        'author': notice.get('author'),
                        'date': notice.get('date'),
                        'views': notice.get('views'),
                    }

                    created_notice = await notice_repo.create(db_session, notice_data)
                    await db_session.commit()
                    result["new"] += 1

                    # 첨부파일 처리
                    if auto_download and notice_detail.get("attachments"):
                        attachment_results = await self.file_handler.download_attachments(
                            self.session, notice_detail, course_id
                        )

                        for attachment in attachment_results:
                            if attachment["success"]:
                                attachment_data = {
                                    "file_name": attachment["file_name"],
                                    "original_url": attachment["original_url"],
                                    "storage_path": attachment.get("storage_path", ""),
                                    "source_id": created_notice.id,
                                    "source_type": "notices",
                                    "course_id": course_id,
                                    "user_id": user_id,  # Add user_id for compatibility
                                }
                                await attachment_repo.create(db_session, attachment_data)
                                await db_session.commit()

                except Exception as e:
                    logger.error(f"공지사항 {article_id} 처리 중 오류: {str(e)}")
                    result["errors"] += 1

            return result

        except Exception as e:
            logger.error(f"공지사항 크롤링 중 오류 발생: {str(e)}")
            result["errors"] += 1
            return result

    async def _crawl_materials(self, user_id: str, course_id: str, material_url: str, db_session,
                               auto_download: bool) -> Dict[str, Any]:
        """강의자료 크롤링"""
        result = {"count": 0, "new": 0, "errors": 0}

        try:
            base_url = "https://eclass.seoultech.ac.kr"
            material_url = f"{base_url}{material_url}" if not material_url.startswith("http") else material_url
            material_url = material_url.replace('lecture_material_list_form', 'lecture_material_list')

            response = await self.session.get(material_url)

            if not response:
                return result

            materials = self.parser.parse_material_list(response.text)

            if not materials:
                logger.warning(f"강의 {course_id}의 강의자료가 없습니다.")
                return result

            # 기존 강의자료 조회
            material_repo = MaterialRepository()
            attachment_repo = AttachmentRepository()

            existing_materials = await material_repo.get_by_course_id(db_session, course_id)
            existing_article_ids = {material.article_id for material in existing_materials}

            # 새 강의자료 처리
            for material in materials:
                result["count"] += 1
                article_id = material.get("article_id")

                logger.debug(f"강의자료 처리 - article_id: {article_id}, title: {material.get('title')}")

                if not article_id:
                    result["errors"] += 1
                    continue

                try:
                    # 이미 존재하는 강의자료면 건너뜀
                    if article_id in existing_article_ids:
                        logger.debug(f"이미 존재하는 강의자료 건너뛰기: {article_id}")
                        continue

                    # 강의자료 상세 정보 가져오기
                    logger.debug(f"강의자료 상세 정보 요청 URL: {material['url']}")
                    detail_response = await self.session.get(material["url"])

                    if not detail_response:
                        logger.error(f"강의자료 상세 정보 응답 없음: {article_id}")
                        result["errors"] += 1
                        continue

                    if detail_response:
                        # HTTP 세션(self.session)을 전달
                        material_detail = await self.parser.parse_material_detail(
                            self.session,
                            detail_response.text,
                            course_id
                        )
                        material.update(material_detail)


                    # 상세 페이지 HTML 저장
                    # 테스트를 위한 임시 저장
                    try:
                        save_dir = os.path.join("html_dumps", "materials", course_id, article_id)
                        os.makedirs(save_dir, exist_ok=True)

                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"material_detail_{timestamp}.html"
                        file_path = os.path.join(save_dir, filename)

                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(detail_response.text)
                        logger.debug(f"강의자료 상세 HTML 저장 완료: {file_path}")
                    except Exception as e:
                        logger.error(f"상세 HTML 저장 중 오류: {str(e)}")

                    logger.debug(f"강의자료 상세 정보 응답 받음: {bool(detail_response.text)}")
                    material_detail = await self.parser.parse_material_detail(self.session, detail_response.text, course_id)
                    logger.debug(f"강의자료 상세 정보 파싱 결과: {material_detail}")

                    # 강의자료 정보 병합
                    material.update(material_detail)
                    filtered_material_data = {
                        "article_id": material.get("article_id"),
                        "course_id": course_id,
                        "title": material.get("title"),
                        "content": material.get("content"),
                        "author": material.get("author"),
                        "date": material.get("date"),
                        "views": material.get("views"),
                    }

                    # DB에 저장
                    logger.debug(f"강의자료 DB 저장 시도: {filtered_material_data}")
                    created_material = await material_repo.create(db_session, filtered_material_data)
                    logger.info(f"새 강의자료 저장 완료: {created_material.id}")
                    result["new"] += 1

                    # 첨부파일 처리
                    if auto_download and "attachments" in material and material["attachments"]:
                        logger.debug(f"첨부파일 다운로드 시작: {len(material['attachments'])}개")
                        attachment_results = await self.file_handler.download_attachments(
                            self.session, material, course_id
                        )
                        logger.debug(f"첨부파일 다운로드 결과: {attachment_results}")

                        # 첨부파일 정보 저장
                        for attachment in attachment_results:
                            if attachment["success"]:
                                try:
                                    attachment_data = {
                                        "file_name": attachment["file_name"],
                                        "original_url": attachment["original_url"],
                                        "storage_path": attachment.get("storage_path", ""),
                                        "source_id": str(created_material.id),
                                        "source_type": "lecture_materials",
                                        "course_id": course_id,
                                        "user_id": user_id,  # Add user_id for compatibility
                                    }
                                    await attachment_repo.create(db_session, attachment_data)
                                    logger.debug(f"첨부파일 메타데이터 저장 완료: {attachment['file_name']}")
                                except Exception as e:
                                    logger.error(f"첨부파일 메타데이터 저장 실패: {str(e)}")

                except Exception as e:
                    logger.error(f"강의자료 {article_id} 처리 중 오류: {str(e)}")
                    result["errors"] += 1

            logger.info(f"강의자료 크롤링 완료 - 총: {result['count']}, 신규: {result['new']}, 오류: {result['errors']}")
            return result

        except Exception as e:
            logger.error(f"강의자료 크롤링 중 오류 발생: {str(e)}")
            result["errors"] += 1
            return result

    async def _crawl_assignments(self, user_id: str, course_id: str, assignment_url: str, db_session,
                                 auto_download: bool) -> Dict[str, Any]:
        """
        과제 크롤링

        Args:
            user_id: 사용자 ID
            course_id: 강의 ID
            assignment_url: 과제 URL
            db_session: 데이터베이스 세션
            auto_download: 첨부파일 자동 다운로드 여부

        Returns:
            Dict[str, Any]: 과제 크롤링 결과
        """
        result = {"count": 0, "new": 0, "errors": 0}

        try:
            # 과제 페이지 접근
            base_url = "https://eclass.seoultech.ac.kr"
            assignment_url = f"{base_url}{assignment_url}" if not assignment_url.startswith("http") else assignment_url

            response = await self.session.get(assignment_url)
            assignments = self.parser.parse_assignment_list(response.text)

            if not assignments:
                logger.info(f"강의 {course_id}의 과제가 없습니다.")
                return result

            # 기존 과제 조회
            assignment_repo = AssignmentRepository()
            attachment_repo = AttachmentRepository()

            existing_assignments = await assignment_repo.get_by_course_id(db_session, course_id)
            existing_assignment_ids = {assignment.assignment_id for assignment in existing_assignments}

            # 새 과제 처리
            for assignment in assignments:
                result["count"] += 1
                assignment_id = assignment.get("assignment_id")

                if not assignment_id:
                    result["errors"] += 1
                    continue

                try:
                    # 이미 존재하는 과제면 건너뜀
                    if assignment_id in existing_assignment_ids:
                        continue

                    # 과제 상세 정보 가져오기
                    detail_response = await self.session.get(assignment["url"])
                    assignment_detail = self.parser.parse_assignment_detail(detail_response.text)

                    # 과제 정보 병합
                    assignment.update(assignment_detail)
                    assignment["course_id"] = course_id
                    assignment["user_id"] = user_id
                    assignment["type"] = "assignments"

                    # DB에 저장
                    created_assignment = await assignment_repo.create(db_session, assignment)
                    result["new"] += 1

                    # 첨부파일 처리
                    if auto_download and "attachments" in assignment and assignment["attachments"]:
                        attachment_results = await self.file_handler.download_attachments(
                            self.session, assignment, course_id
                        )

                        # 첨부파일 정보 저장
                        for attachment in attachment_results:
                            # 첨부파일 저장 전 중복 검증
                            await self.verify_duplicate_attachment(
                                db_session,
                                attachment["file_name"],
                                attachment["original_url"],
                                str(created_assignment.id),  # or created_material.id, created_assignment.id
                                course_id
                            )

                            if attachment["success"]:
                                attachment_data = {
                                    "file_name": attachment["file_name"],
                                    "original_url": attachment["original_url"],  # Add original_url for consistency
                                    "storage_path": attachment.get("storage_path", ""),
                                    "source_id": str(created_assignment.id),
                                    "source_type": "assignments",
                                    "course_id": course_id,
                                    "user_id": user_id,  # Add user_id for compatibility
                                }
                                await attachment_repo.create(db_session, attachment_data)

                except Exception as e:
                    logger.error(f"과제 {assignment_id} 처리 중 오류: {e}")
                    result["errors"] += 1

            return result

        except Exception as e:
            logger.error(f"과제 크롤링 중 오류 발생: {e}")
            result["errors"] += 1
            return result

    async def crawl_all_courses(self, user_id: str, db_session, auto_download: bool = False) -> Dict[str, Any]:
        """
        모든 강의 크롤링

        Args:
            user_id: 사용자 ID
            db_session: 데이터베이스 세션
            auto_download: 첨부파일 자동 다운로드 여부

        Returns:
            Dict[str, Any]: 크롤링 작업 정보
        """
        # 작업 ID 생성
        task_id = f"crawl_all_{uuid.uuid4().hex[:8]}"

        logger.info(f"모든 강의 크롤링 작업 시작: {task_id} (사용자: {user_id})")

        # 로그인 상태 확인 및 자동 로그인 시도
        if not await self.ensure_logged_in():
            logger.error("e-Class 로그인 실패")
            return {
                "task_id": task_id,
                "status": "error",
                "message": "e-Class 로그인 실패"
            }

        # 강의 목록 가져오기
        courses = await self.get_courses(user_id, db_session, force_refresh=True)

        if not courses:
            logger.warning("크롤링할 강의가 없습니다")
            return {
                "task_id": task_id,
                "status": "error",
                "message": "크롤링할 강의가 없습니다",
                "courses": []
            }

        # 작업 시작
        task = asyncio.create_task(
            self._crawl_all_courses_task(user_id, courses, db_session, auto_download, task_id)
        )

        # 작업 관리
        self.active_tasks[task_id] = {
            "task": task,
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "user_id": user_id,
            "auto_download": auto_download,
            "course_count": len(courses)
        }

        return {
            "task_id": task_id,
            "status": "running",
            "message": f"모든 강의 크롤링 작업이 시작되었습니다 ({len(courses)}개)",
            "courses": [course.name for course in courses]
        }

    async def get_notices(self, user_id: str, course_id: str, db_session) -> List[Dict[str, Any]]:
        """
        특정 강의의 공지사항 조회

        Args:
            user_id: 사용자 ID
            course_id: 강의 ID
            db_session: 데이터베이스 세션

        Returns:
            List[Dict[str, Any]]: 공지사항 목록
        """
        logger.info(f"사용자 {user_id}의 강의 {course_id} 공지사항 조회")

        # 레포지토리 초기화
        notice_repo = NoticeRepository()
        attachment_repo = AttachmentRepository()

        # 저장된 공지사항 가져오기
        notices = await notice_repo.get_by_course_id(db_session, course_id)

        # 공지사항 정보와 첨부파일 정보 조합
        result = []
        for notice in notices:
            notice_dict = notice.to_dict()

            # 첨부파일 조회
            attachments = await attachment_repo.get_by_source(db_session, notice.id, "notices")
            notice_dict["attachments"] = [attachment.to_dict() for attachment in attachments]

            result.append(notice_dict)

        logger.info(f"강의 {course_id}의 공지사항 {len(result)}개 반환")
        return result

    async def get_materials(self, user_id: str, course_id: str, db_session) -> List[Dict[str, Any]]:
        """
        특정 강의의 강의자료 조회

        Args:
            user_id: 사용자 ID
            course_id: 강의 ID
            db_session: 데이터베이스 세션

        Returns:
            List[Dict[str, Any]]: 강의자료 목록
        """
        logger.info(f"사용자 {user_id}의 강의 {course_id} 강의자료 조회")

        # 레포지토리 초기화
        material_repo = MaterialRepository()
        attachment_repo = AttachmentRepository()

        # 저장된 강의자료 가져오기
        materials = await material_repo.get_by_course_id(db_session, course_id)

        # 강의자료 정보와 첨부파일 정보 조합
        result = []
        for material in materials:
            material_dict = material.to_dict()

            # 첨부파일 조회
            attachments = await attachment_repo.get_by_source(db_session, material.id, "lecture_materials")
            material_dict["attachments"] = [attachment.to_dict() for attachment in attachments]

            result.append(material_dict)

        logger.info(f"강의 {course_id}의 강의자료 {len(result)}개 반환")
        return result

    async def get_assignments(self, user_id: str, course_id: str, db_session) -> List[Dict[str, Any]]:
        """
        특정 강의의 과제 조회

        Args:
            user_id: 사용자 ID
            course_id: 강의 ID
            db_session: 데이터베이스 세션

        Returns:
            List[Dict[str, Any]]: 과제 목록
        """
        logger.info(f"사용자 {user_id}의 강의 {course_id} 과제 조회")

        # 레포지토리 초기화
        assignment_repo = AssignmentRepository()
        attachment_repo = AttachmentRepository()

        # 저장된 과제 가져오기
        assignments = await assignment_repo.get_by_course_id(db_session, course_id)

        # 과제 정보와 첨부파일 정보 조합
        result = []
        for assignment in assignments:
            assignment_dict = assignment.to_dict()

            # 첨부파일 조회
            attachments = await attachment_repo.get_by_source(db_session, assignment.id, "assignments")
            assignment_dict["attachments"] = [attachment.to_dict() for attachment in attachments]

            result.append(assignment_dict)

        logger.info(f"강의 {course_id}의 과제 {len(result)}개 반환")
        return result

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        작업 상태 조회

        Args:
            task_id: 작업 ID

        Returns:
            Dict[str, Any]: 작업 상태 정보
        """
        logger.info(f"작업 {task_id} 상태 조회")

        if task_id not in self.active_tasks:
            logger.warning(f"존재하지 않는 작업 ID: {task_id}")
            return {
                "task_id": task_id,
                "status": "not_found",
                "message": "존재하지 않는 작업입니다."
            }

        task_info = self.active_tasks[task_id]
        result = {
            "task_id": task_id,
            "status": task_info["status"],
        }

        # 추가 정보가 있으면 포함
        for key in ["start_time", "end_time", "course_id", "user_id", "message", "result"]:
            if key in task_info:
                result[key] = task_info[key]

        return result

    async def cancel_task(self, task_id: str) -> bool:
        """

        작업 취소

        Args:
            task_id: 작업 ID

        Returns:
            bool: 취소 성공 여부
        """
        logger.info(f"작업 {task_id} 취소 요청")

        if task_id not in self.active_tasks:
            logger.warning(f"존재하지 않는 작업 ID: {task_id}")
            return False

        task_info = self.active_tasks[task_id]

        # 이미 완료된 작업은 취소할 수 없음
        if task_info["status"] in ["completed", "failed", "canceled"]:
            logger.warning(f"이미 {task_info['status']} 상태인 작업은 취소할 수 없습니다: {task_id}")
            return False

        # 작업 취소 - AsyncMock를 위해 await 없이 직접 호출
        if "task" in task_info and not task_info["task"].done():
            task_info["task"].cancel()
            await asyncio.sleep(0)  # 태스크 상태 반영 대기

        # 상태 업데이트
        task_info["status"] = "canceled"
        task_info["end_time"] = datetime.now().isoformat()

        logger.info(f"작업 {task_id} 취소 완료")
        return True

    # close 메서드 수정 제안
    async def close(self) -> None:
        """
        서비스 종료 및 리소스 정리
        """
        logger.info("EclassService 종료 시작")

        # 실행 중인 모든 작업 취소
        for task_id, task_info in self.active_tasks.items():
            if task_info.get("status") in ["running", "processing"]:
                if "task" in task_info and not task_info["task"].done():
                    logger.info(f"작업 {task_id} 취소")
                    task_info["task"].cancel()
                    await asyncio.sleep(0)  # 태스크 상태 반영 대기

                task_info["status"] = "canceled"
                task_info["end_time"] = datetime.now().isoformat()

        # 세션 종료
        await self.session.close()
        logger.info("EclassService 종료 완료")

    async def _crawl_all_courses_task(self, user_id: str, courses: List[Dict[str, Any]], db_session,
                                      auto_download: bool, task_id: str) -> Dict[str, Any]:
        """
        모든 강의 크롤링 작업 수행

        Args:
            user_id: 사용자 ID
            courses: 강의 목록
            db_session: 데이터베이스 세션
            auto_download: 첨부파일 자동 다운로드 여부
            task_id: 작업 ID

        Returns:
            Dict[str, Any]: 크롤링 결과
        """
        try:
            # 작업 상태 업데이트
            self.active_tasks[task_id]["status"] = "processing"

            # 크롤링 결과 저장
            result = {
                "task_id": task_id,
                "user_id": user_id,
                "status": "success",
                "timestamp": datetime.now().isoformat(),
                "course_results": {},
                "summary": {
                    "total_courses": len(courses),
                    "completed": 0,
                    "failed": 0,
                    "notices": {"count": 0, "new": 0, "errors": 0},
                    "materials": {"count": 0, "new": 0, "errors": 0},
                    "assignments": {"count": 0, "new": 0, "errors": 0},
                    "attachments": {"count": 0, "success": 0, "errors": 0}
                }
            }

            # 각 강의 순차적으로 크롤링
            for course in courses:

                try:
                    course_id = course.id

                    # 개별 강의 크롤링
                    course_result = await self._crawl_course_task(
                        user_id, course_id, db_session, auto_download, f"{task_id}_{course_id}"
                    )

                    # 결과 저장
                    result["course_results"][course_id] = {
                        "name": course.name,
                        "code": course.code,
                        "status": course_result["status"],
                        "details": course_result.get("details", {})
                    }

                    # 요약 정보 업데이트
                    if course_result["status"] == "success":
                        result["summary"]["completed"] += 1
                        details = course_result.get("details", {})

                        for category in ["notices", "materials", "assignments"]:
                            if category in details:
                                for key in ["count", "new", "errors"]:
                                    result["summary"][category][key] += details[category].get(key, 0)
                    else:
                        result["summary"]["failed"] += 1


                except Exception as e:
                    logger.error(f"강의 {course_id} 크롤링 중 오류: {e}")
                    result["course_results"][course_id] = {
                        "name": course.name,
                        "code": course.code,
                        "status": "error",
                        "message": str(e)
                    }
                    result["summary"]["failed"] += 1

            # 작업 완료
            self.active_tasks[task_id]["status"] = "completed"
            self.active_tasks[task_id]["end_time"] = datetime.now().isoformat()
            self.active_tasks[task_id]["result"] = result

            logger.info(f"모든 강의 크롤링 작업 완료: {task_id}")
            return result

        except Exception as e:
            logger.exception(f"모든 강의 크롤링 작업 중 오류 발생: {e}")

            # 작업 실패
            self.active_tasks[task_id]["status"] = "failed"
            self.active_tasks[task_id]["error"] = str(e)
            self.active_tasks[task_id]["end_time"] = datetime.now().isoformat()

            return {
                "task_id": task_id,
                "user_id": user_id,
                "status": "error",
                "message": f"크롤링 중 오류 발생: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    async def get_syllabus(self, user_id: str, course_id: str, db: AsyncSession) -> Dict[str, Any]:
        """
        강의계획서 조회

        Args:
            user_id: 사용자 ID
            course_id: 강의 ID
            db: 데이터베이스 세션

        Returns:
            Dict[str, Any]: 강의계획서 정보
        """
        logger.info(f"강의 {course_id}의 강의계획서 조회 시작")

        try:
            # 강의계획서 URL 구성
            base_url = "https://eclass.seoultech.ac.kr"
            syllabus_url = f"{base_url}/lecture/course_info.jsp?ref=1&ud={user_id}&ky={course_id}"

            # 강의계획서 페이지 요청
            response = await self.session.get(syllabus_url)
            if not response:
                logger.error("강의계획서 페이지 요청 실패")
                return {}

            # 강의계획서 파싱
            syllabus_data = self.parser.parse_syllabus(response.text)
            logger.info(f"강의계획서 파싱 완료: {syllabus_data}")

            return syllabus_data

        except Exception as e:
            logger.error(f"강의계획서 조회 중 오류 발생: {str(e)}")
            raise
