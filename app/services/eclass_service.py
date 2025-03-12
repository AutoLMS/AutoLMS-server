import logging
import asyncio
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Set

from app.services.eclass_session import EclassSession
from app.services.eclass_parser import EclassParser
from app.services.file_handler import FileHandler
from app.db.repositories.course_repository import CourseRepository
from app.db.repositories.notice_repository import NoticeRepository
from app.db.repositories.material_repository import MaterialRepository
from app.db.repositories.assignment_repository import AssignmentRepository
from app.db.repositories.attachment_repository import AttachmentRepository

logger = logging.getLogger(__name__)


class EclassService:
    """통합 e-Class 서비스"""

    def __init__(self, session=None, parser=None, file_handler=None):
        """EclassService 초기화"""
        self.session = session or EclassSession()
        self.parser = parser or EclassParser()
        self.file_handler = file_handler or FileHandler()

        # 작업 관리
        self.active_tasks = {}

    async def login(self, username: str, password: str) -> bool:
        """e-Class 로그인"""
        return await self.session.login(username, password)

    async def is_logged_in(self) -> bool:
        """로그인 상태 확인"""
        return await self.session.is_logged_in()

    async def get_courses(self, user_id: str, db_session, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        강의 목록 조회 및 DB 동기화

        Args:
            user_id: 사용자 ID
            db_session: 데이터베이스 세션
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
        course_repo = CourseRepository(db_session)
        existing_courses = await course_repo.get_by_user_id(user_id)

        # 강제 새로고침이 아니고 저장된 강의가 있으면 그대로 반환
        if not force_refresh and existing_courses:
            logger.info(f"저장된 강의 목록 반환: {len(existing_courses)}개")
            return [course.to_dict() for course in existing_courses]

        # e-Class에서 강의 목록 가져오기
        html = await self.session.get_course_list()
        courses = self.parser.parse_courses(html)

        if not courses:
            logger.warning("e-Class에서 가져온 강의 목록이 비어 있습니다")
            return []

        # 데이터베이스에 강의 정보 저장
        existing_course_ids = {course.eclass_id for course in existing_courses}
        updated_courses = []

        for course in courses:
            course_id = course['id']
            course_dict = {
                'eclass_id': course_id,
                'user_id': user_id,
                'name': course['name'],
                'code': course['code'],
                'time': course.get('time', ''),
                'last_updated': datetime.now()
            }

            if course_id in existing_course_ids:
                # 기존 강의 업데이트
                updated_course = await course_repo.update(course_id, course_dict)
                updated_courses.append(updated_course.to_dict())
            else:
                # 새 강의 추가
                new_course = await course_repo.create(course_dict)
                updated_courses.append(new_course.to_dict())

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

        # 로그인 상태 확인
        if not await self.is_logged_in():
            logger.error("로그인되지 않은 상태에서 크롤링 시도")
            return {
                "task_id": task_id,
                "status": "error",
                "message": "로그인이 필요합니다",
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
            self.active_tasks[task_id]["status"] = "completed"
            self.active_tasks[task_id]["end_time"] = datetime.now().isoformat()
            self.active_tasks[task_id]["result"] = result

            logger.info(f"강의 크롤링 작업 완료: {task_id}")
            return result

        except Exception as e:
            logger.exception(f"강의 크롤링 작업 중 오류 발생: {e}")

            # 작업 실패
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
        """
        공지사항 크롤링

        Args:
            user_id: 사용자 ID
            course_id: 강의 ID
            notice_url: 공지사항 URL
            db_session: 데이터베이스 세션
            auto_download: 첨부파일 자동 다운로드 여부

        Returns:
            Dict[str, Any]: 공지사항 크롤링 결과
        """
        result = {"count": 0, "new": 0, "errors": 0}

        try:
            # 공지사항 페이지 접근
            base_url = "https://eclass.seoultech.ac.kr"
            notice_url = f"{base_url}{notice_url}" if not notice_url.startswith("http") else notice_url

            response = await self.session.get(notice_url)
            notices = self.parser.parse_notice_list(response.text)

            if not notices:
                logger.info(f"강의 {course_id}의 공지사항이 없습니다.")
                return result

            # 기존 공지사항 조회
            notice_repo = NoticeRepository(db_session)
            attachment_repo = AttachmentRepository(db_session)

            existing_notices = await notice_repo.get_by_course_id(course_id)
            existing_article_ids = {notice.article_id for notice in existing_notices}

            # 새 공지사항 처리
            for notice in notices:
                result["count"] += 1
                article_id = notice.get("article_id")

                if not article_id:
                    result["errors"] += 1
                    continue

                try:
                    # 이미 존재하는 공지사항이면 건너뜀
                    if article_id in existing_article_ids:
                        continue

                    # 공지사항 상세 정보 가져오기
                    detail_response = await self.session.get(notice["url"])
                    notice_detail = self.parser.parse_notice_detail(detail_response.text)

                    # 공지사항 정보 병합
                    notice.update(notice_detail)
                    notice["course_id"] = course_id
                    notice["user_id"] = user_id
                    notice["type"] = "notices"

                    # DB에 저장
                    created_notice = await notice_repo.create(notice)
                    result["new"] += 1

                    # 첨부파일 처리
                    if auto_download and "attachments" in notice and notice["attachments"]:
                        attachment_results = await self.file_handler.download_attachments(
                            self.session, notice, course_id
                        )

                        # 첨부파일 정보 저장
                        for attachment in attachment_results:
                            if attachment["success"]:
                                attachment_data = {
                                    "name": attachment["name"],
                                    "original_url": attachment["original_url"],
                                    "storage_url": attachment.get("storage_url", ""),
                                    "local_path": attachment.get("local_path", ""),
                                    "source_id": created_notice.id,
                                    "source_type": "notices",
                                    "course_id": course_id,
                                    "user_id": user_id
                                }
                                await attachment_repo.create(attachment_data)

                except Exception as e:
                    logger.error(f"공지사항 {article_id} 처리 중 오류: {e}")
                    result["errors"] += 1

            return result

        except Exception as e:
            logger.error(f"공지사항 크롤링 중 오류 발생: {e}")
            result["errors"] += 1
            return result

    async def _crawl_materials(self, user_id: str, course_id: str, material_url: str, db_session,
                               auto_download: bool) -> Dict[str, Any]:
        """
        강의자료 크롤링

        Args:
            user_id: 사용자 ID
            course_id: 강의 ID
            material_url: 강의자료 URL
            db_session: 데이터베이스 세션
            auto_download: 첨부파일 자동 다운로드 여부

        Returns:
            Dict[str, Any]: 강의자료 크롤링 결과
        """
        result = {"count": 0, "new": 0, "errors": 0}

        try:
            # 강의자료 페이지 접근
            base_url = "https://eclass.seoultech.ac.kr"
            material_url = f"{base_url}{material_url}" if not material_url.startswith("http") else material_url

            response = await self.session.get(material_url)
            materials = self.parser.parse_material_list(response.text)

            if not materials:
                logger.info(f"강의 {course_id}의 강의자료가 없습니다.")
                return result

            # 기존 강의자료 조회
            material_repo = MaterialRepository(db_session)
            attachment_repo = AttachmentRepository(db_session)

            existing_materials = await material_repo.get_by_course_id(course_id)
            existing_article_ids = {material.article_id for material in existing_materials}

            # 새 강의자료 처리
            for material in materials:
                result["count"] += 1
                article_id = material.get("article_id")

                if not article_id:
                    result["errors"] += 1
                    continue

                try:
                    # 이미 존재하는 강의자료면 건너뜀
                    if article_id in existing_article_ids:
                        continue

                    # 강의자료 상세 정보 가져오기
                    detail_response = await self.session.get(material["url"])
                    material_detail = self.parser.parse_material_detail(detail_response.text)

                    # 강의자료 정보 병합
                    material.update(material_detail)
                    material["course_id"] = course_id
                    material["user_id"] = user_id
                    material["type"] = "lecture_materials"

                    # DB에 저장
                    created_material = await material_repo.create(material)
                    result["new"] += 1

                    # 첨부파일 처리
                    if auto_download and "attachments" in material and material["attachments"]:
                        attachment_results = await self.file_handler.download_attachments(
                            self.session, material, course_id
                        )

                        # 첨부파일 정보 저장
                        for attachment in attachment_results:
                            if attachment["success"]:
                                attachment_data = {
                                    "name": attachment["name"],
                                    "original_url": attachment["original_url"],
                                    "storage_url": attachment.get("storage_url", ""),
                                    "local_path": attachment.get("local_path", ""),
                                    "source_id": created_material.id,
                                    "source_type": "lecture_materials",
                                    "course_id": course_id,
                                    "user_id": user_id
                                }
                                await attachment_repo.create(attachment_data)

                except Exception as e:
                    logger.error(f"강의자료 {article_id} 처리 중 오류: {e}")
                    result["errors"] += 1

            return result

        except Exception as e:
            logger.error(f"강의자료 크롤링 중 오류 발생: {e}")
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
            assignment_repo = AssignmentRepository(db_session)
            attachment_repo = AttachmentRepository(db_session)

            existing_assignments = await assignment_repo.get_by_course_id(course_id)
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
                    created_assignment = await assignment_repo.create(assignment)
                    result["new"] += 1

                    # 첨부파일 처리
                    if auto_download and "attachments" in assignment and assignment["attachments"]:
                        attachment_results = await self.file_handler.download_attachments(
                            self.session, assignment, course_id
                        )

                        # 첨부파일 정보 저장
                        for attachment in attachment_results:
                            if attachment["success"]:
                                attachment_data = {
                                    "name": attachment["name"],
                                    "original_url": attachment["original_url"],
                                    "storage_url": attachment.get("storage_url", ""),
                                    "local_path": attachment.get("local_path", ""),
                                    "source_id": created_assignment.id,
                                    "source_type": "assignments",
                                    "course_id": course_id,
                                    "user_id": user_id
                                }
                                await attachment_repo.create(attachment_data)

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

        # 로그인 상태 확인
        if not await self.is_logged_in():
            logger.error("로그인되지 않은 상태에서 크롤링 시도")
            return {
                "task_id": task_id,
                "status": "error",
                "message": "로그인이 필요합니다"
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
            "courses": [course["name"] for course in courses]
        }

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
                course_id = course["eclass_id"]

                try:
                    # 개별 강의 크롤링
                    course_result = await self._crawl_course_task(
                        user_id, course_id, db_session, auto_download, f"{task_id}_{course_id}"
                    )

                    # 결과 저장
                    result["course_results"][course_id] = {
                        "name": course["name"],
                        "code": course["code"],
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
                        "name": course["name"],
                        "code": course["code"],
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