import asyncio
import logging
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any

from app.db.repositories.supabase_assignment_repository import SupabaseAssignmentRepository
from app.db.repositories.supabase_attachment_repository import SupabaseAttachmentRepository
from app.db.repositories.supabase_material_repository import SupabaseMaterialRepository
# Supabase Repository imports
from app.db.repositories.supabase_notice_repository import SupabaseNoticeRepository
from app.db.repositories.supabase_syllabus_repository import SupabaseSyllabusRepository
from app.services.eclass_parser import EclassParser
from app.services.eclass_session import EclassSession
from app.services.file_handler import FileHandler

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

    async def get_courses(self, user_id: str, force_refresh: bool = False, is_jwt_user: bool = False) -> List[Dict[str, Any]]:
        """
        강의 목록 조회 및 DB 동기화

        Args:
            user_id: 사용자 ID
            force_refresh: 강제 새로고침 여부
            is_jwt_user: JWT 기반 사용자 여부

        Returns:
            List[Dict[str, Any]]: 강의 목록
        """
        logger.info(f"사용자 {user_id}의 강의 목록 조회 시작")

        # 로그인 상태 확인
        if not await self.is_logged_in():
            logger.error("로그인되지 않은 상태에서 강의 목록 조회 시도")
            return []

        # 이미 저장된 강의 목록 가져오기 - JWT 사용자는 Service Key 사용
        from app.db.repositories.supabase_course_repository import SupabaseCourseRepository
        course_repo = SupabaseCourseRepository(use_service_key=is_jwt_user)
        existing_courses = await course_repo.get_by_user_id(user_id)

        # 강제 새로고침이 아니고 저장된 강의가 있으면 Course 스키마 형식으로 변환하여 반환
        if not force_refresh and existing_courses:
            logger.info(f"저장된 강의 목록 반환: {len(existing_courses)}개")
            return self._transform_db_courses_to_schema(existing_courses)

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
        existing_course_ids = {course.get('course_id') for course in existing_courses if course}
        updated_courses = []

        for course in courses:
            # Supabase 테이블 전체 필드 사용
            course_dict = {
                'course_id': course.get('id'),  # 원래 강의 ID
                'user_id': user_id,
                'course_name': course.get('name', ''),
                'instructor': course.get('instructor', ''),  # 교수님 이름
                'semester': course.get('semester') if course.get('semester') else None,  # 학기 정보
                'year': int(course.get('year')) if course.get('year') and course.get('year').isdigit() else None,  # 연도 정보
                'last_crawled': datetime.now().isoformat(),  # 마지막 크롤링 시간
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }

            try:
                if course['id'] in existing_course_ids:
                    # 기존 강의 업데이트 (course_id로 찾기)
                    existing_course = next(c for c in existing_courses if c.get('course_id') == course['id'])
                    # course_id 제외하고 업데이트 (이미 존재하므로)
                    update_dict = {k: v for k, v in course_dict.items() if k != 'course_id'}
                    updated_course = await course_repo.update(existing_course['id'], **update_dict)
                    if updated_course:
                        updated_courses.append(updated_course)
                else:
                    # 새 강의 추가 (course_dict에서 user_id 제거)
                    course_data = {k: v for k, v in course_dict.items() if k != 'user_id'}
                    new_course = await course_repo.upsert_with_user_enrollment(user_id, **course_data)
                    if new_course:
                        updated_courses.append(new_course)
            except Exception as e:
                logger.error(f"강의 정보 저장 중 오류 발생: {str(e)}")
                continue

        logger.info(f"강의 목록 동기화 완료: {len(updated_courses)}개")
        return self._transform_db_courses_to_schema(updated_courses)

    def _transform_db_courses_to_schema(self, db_courses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        데이터베이스 강의 데이터를 Course 스키마 형식으로 변환
        
        Args:
            db_courses: 데이터베이스에서 가져온 강의 데이터 리스트
            
        Returns:
            List[Dict[str, Any]]: Course 스키마와 호환되는 데이터 리스트
        """
        transformed_courses = []
        
        for course in db_courses:
            if not course:
                continue
                
            # 데이터베이스 필드를 Course 스키마 필드로 매핑
            transformed_course = {
                'id': course.get('course_id', course.get('id', '')),  # course_id를 id로 사용
                'name': course.get('course_name', course.get('name', '')),  # course_name을 name으로 사용
                'code': course.get('code', course.get('instructor', '')),  # instructor를 임시로 code로 사용 (또는 빈 문자열)
                'time': course.get('time', course.get('semester', '')),  # semester를 임시로 time으로 사용 (또는 빈 문자열)
                'created_at': course.get('created_at', datetime.now()),
                'updated_at': course.get('updated_at', datetime.now())
            }
            
            # datetime 타입으로 변환이 필요한 경우
            for field in ['created_at', 'updated_at']:
                if isinstance(transformed_course[field], str):
                    try:
                        transformed_course[field] = datetime.fromisoformat(transformed_course[field].replace('Z', '+00:00'))
                    except:
                        transformed_course[field] = datetime.now()
            
            transformed_courses.append(transformed_course)
            
        return transformed_courses

    async def crawl_course(self, user_id: str, course_id: str, auto_download: bool = False, is_jwt_user: bool = False) -> Dict[
        str, Any]:
        """
        특정 강의 크롤링 작업 시작

        Args:
            user_id: 사용자 ID
            course_id: 강의 ID
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
            self._crawl_course_task(user_id, course_id, auto_download, task_id, is_jwt_user)
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

    async def _crawl_course_task(self, user_id: str, course_id: str, auto_download: bool, task_id: str, is_jwt_user: bool = False) -> \
            Dict[str, Any]:
        """
        강의 크롤링 작업 수행

        Args:
            user_id: 사용자 ID
            course_id: 강의 ID
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
                    "syllabus": {"count": 0, "new": 0, "errors": 0},
                    "attachments": {"count": 0, "success": 0, "errors": 0}
                }
            }

            # 강의실 접근
            logger.info(f"강의 {course_id} 접근 시도")
            course_url = await self.session.access_course(course_id)
            if not course_url:
                logger.error(f"강의실 접근 실패: {course_id}")
                result["status"] = "error"
                result["message"] = "강의실 접근 실패"
                return result
            
            logger.info(f"강의실 URL 획득: {course_url}")

            # 강의 메뉴 확인
            logger.info(f"강의 {course_id} 메뉴 페이지 요청")
            response = await self.session.get(course_url)
            logger.info(f"메뉴 페이지 응답 길이: {len(response.text)}")
            
            course_menus = self.parser.parse_course_menus(response.text)
            logger.info(f"파싱된 강의 메뉴: {course_menus}")
            
            if not course_menus:
                logger.warning(f"강의 {course_id}에서 메뉴를 찾을 수 없음")
                result["message"] = "강의 메뉴를 찾을 수 없습니다"

            # 공지사항 크롤링
            if "notice" in course_menus:
                notice_result = await self._crawl_notices(
                    user_id, course_id, course_menus["notice"]["url"], auto_download
                )
                result["details"]["notices"] = notice_result

            # 강의자료 크롤링
            if "lecture_material" in course_menus:
                material_result = await self._crawl_materials(
                    user_id, course_id, course_menus["lecture_material"]["url"], auto_download
                )
                result["details"]["materials"] = material_result

            # 과제 크롤링
            if "assignment" in course_menus:
                assignment_result = await self._crawl_assignments(
                    user_id, course_id, course_menus["assignment"]["url"], auto_download
                )
                result["details"]["assignments"] = assignment_result

            # 강의계획서 크롤링
            if "plan" in course_menus:
                syllabus_result = await self._crawl_syllabus(
                    user_id, course_id, course_menus["plan"]["url"]
                )
                result["details"]["syllabus"] = syllabus_result

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

    async def _crawl_notices(self, user_id: str, course_id: str, notice_url: str, auto_download: bool) -> \
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
            notice_repo = SupabaseNoticeRepository()
            attachment_repo = SupabaseAttachmentRepository()
            existing_notices = await notice_repo.get_by_course_id(course_id)
            existing_article_ids = {notice['article_id'] for notice in existing_notices}

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

                    # DB 저장 (스키마 수정 후)
                    notice_data = {
                        'article_id': article_id,  # article_id 컬럼 사용
                        'user_id': user_id,        # user_id 필수
                        'course_id': course_id,    # course_id를 문자열로 그대로 사용
                        'title': notice.get('title'),
                        'content': notice_detail.get('content'),
                        'author': notice.get('author'),
                        'date': notice.get('date'),
                        'views': notice.get('views', 0),
                    }

                    created_notice = await notice_repo.create(**notice_data)
                    result["new"] += 1

                    # 첨부파일 메타데이터 처리 (항상 실행)
                    if notice_detail.get("attachments"):
                        logger.debug(f"공지사항 첨부파일 메타데이터 처리: {len(notice_detail['attachments'])}개")
                        
                        # 실제 파일 다운로드는 auto_download가 True일 때만
                        if auto_download:
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
                                        "user_id": user_id,
                                    }
                                    await attachment_repo.create(**attachment_data)
                        else:
                            # auto_download=False인 경우에도 첨부파일 메타데이터만 저장
                            for attachment in notice_detail["attachments"]:
                                try:
                                    attachment_data = {
                                        "file_name": attachment.get("name", "Unknown"),
                                        "original_url": attachment.get("url", ""),
                                        "storage_path": "",
                                        "source_id": created_notice.id,
                                        "source_type": "notices",
                                        "course_id": course_id,
                                        "user_id": user_id,
                                    }
                                    await attachment_repo.create(**attachment_data)
                                except Exception as e:
                                    logger.error(f"공지사항 첨부파일 메타데이터 저장 실패: {str(e)}")

                except Exception as e:
                    logger.error(f"공지사항 {article_id} 처리 중 오류: {str(e)}")
                    result["errors"] += 1

            return result

        except Exception as e:
            logger.error(f"공지사항 크롤링 중 오류 발생: {str(e)}")
            result["errors"] += 1
            return result

    async def _crawl_materials(self, user_id: str, course_id: str, material_url: str,
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
            material_repo = SupabaseMaterialRepository()
            attachment_repo = SupabaseAttachmentRepository()

            existing_materials = await material_repo.get_by_course_id(course_id)
            existing_article_ids = {material.get('article_id') for material in existing_materials}

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
                        "article_id": material.get("article_id"),  # article_id 컬럼 사용
                        "user_id": user_id,        # user_id 필수
                        "course_id": course_id,    # course_id를 문자열로 그대로 사용
                        "title": material.get("title"),
                        "content": material.get("content"),
                        "author": material.get("author"),
                        "date": material.get("date"),
                        "views": material.get("views", 0),
                    }

                    # DB에 저장
                    logger.debug(f"강의자료 DB 저장 시도: {filtered_material_data}")
                    created_material = await material_repo.create(**filtered_material_data)
                    if created_material:
                        logger.info(f"새 강의자료 저장 완료: {created_material.get('id', 'unknown')}")
                        result["new"] += 1
                    else:
                        logger.error(f"강의자료 저장 실패: {filtered_material_data.get('article_id', 'unknown')}")
                        result["errors"] += 1

                    # 첨부파일 메타데이터 처리 (항상 실행)
                    if "attachments" in material and material["attachments"]:
                        logger.info(f"📎 첨부파일 메타데이터 처리 시작: {len(material['attachments'])}개")
                        logger.debug(f"첨부파일 목록: {[att.get('name', 'No name') for att in material['attachments']]}")
                        
                        # 실제 파일 다운로드는 auto_download가 True일 때만
                        if auto_download:
                            logger.info(f"💾 첨부파일 다운로드 시작: {len(material['attachments'])}개")
                            try:
                                attachment_results = await self.file_handler.download_attachments(
                                    self.session, material, course_id
                                )
                                logger.info(f"📊 첨부파일 다운로드 결과: {len(attachment_results)}개 처리됨")
                                logger.debug(f"다운로드 결과 상세: {attachment_results}")

                                # 첨부파일 정보 저장
                                successful_saves = 0
                                for attachment in attachment_results:
                                    logger.debug(f"첨부파일 결과 처리: {attachment}")
                                    if attachment.get("success", False):
                                        try:
                                            attachment_data = {
                                                "file_name": attachment["file_name"],
                                                "original_url": attachment["original_url"],
                                                "storage_path": attachment.get("storage_path", ""),
                                                "source_id": str(created_material.get('id', 'unknown')),
                                                "source_type": "lecture_materials",
                                                "course_id": course_id,
                                                "user_id": user_id,
                                            }
                                            logger.info(f"💾 첨부파일 메타데이터 저장 시도: {attachment_data}")
                                            saved_attachment = await attachment_repo.create(**attachment_data)
                                            if saved_attachment:
                                                successful_saves += 1
                                                logger.info(f"✅ 첨부파일 메타데이터 저장 성공: {attachment['file_name']}")
                                            else:
                                                logger.error(f"❌ 첨부파일 메타데이터 저장 실패 (None 반환): {attachment['file_name']}")
                                        except Exception as e:
                                            logger.error(f"❌ 첨부파일 메타데이터 저장 중 예외: {str(e)}")
                                            logger.error(f"   데이터: {attachment_data}")
                                    else:
                                        logger.warning(f"⚠️ 첨부파일 다운로드 실패: {attachment.get('file_name', 'Unknown')}, 오류: {attachment.get('error', 'Unknown error')}")
                                
                                logger.info(f"📊 첨부파일 저장 완료: {successful_saves}/{len(attachment_results)}개 성공")
                            except Exception as e:
                                logger.error(f"❌ 첨부파일 다운로드 처리 중 전체 오류: {str(e)}")
                        else:
                            # auto_download=False인 경우에도 첨부파일 메타데이터만 저장
                            logger.info("📋 auto_download=False이므로 첨부파일 메타데이터만 저장")
                            successful_saves = 0
                            for attachment in material["attachments"]:
                                try:
                                    attachment_data = {
                                        "file_name": attachment.get("name", "Unknown"),
                                        "original_url": attachment.get("url", ""),
                                        "storage_path": "",  # 다운로드하지 않으므로 빈 값
                                        "source_id": str(created_material.get('id', 'unknown')),
                                        "source_type": "lecture_materials", 
                                        "course_id": course_id,
                                        "user_id": user_id,
                                    }
                                    logger.info(f"💾 첨부파일 메타데이터만 저장 시도: {attachment_data}")
                                    saved_attachment = await attachment_repo.create(**attachment_data)
                                    if saved_attachment:
                                        successful_saves += 1
                                        logger.info(f"✅ 첨부파일 메타데이터만 저장 성공: {attachment.get('name', 'Unknown')}")
                                    else:
                                        logger.error(f"❌ 첨부파일 메타데이터 저장 실패 (None 반환): {attachment.get('name', 'Unknown')}")
                                except Exception as e:
                                    logger.error(f"❌ 첨부파일 메타데이터 저장 중 예외: {str(e)}")
                                    logger.error(f"   데이터: {attachment_data}")
                            
                            logger.info(f"📊 첨부파일 메타데이터 저장 완료: {successful_saves}/{len(material['attachments'])}개 성공")
                    else:
                        if "attachments" not in material:
                            logger.debug("📋 material에 attachments 키가 없음")
                        elif not material["attachments"]:
                            logger.debug("📋 material.attachments가 비어있음")
                        else:
                            logger.debug("📋 첨부파일 조건 불만족")

                except Exception as e:
                    logger.error(f"강의자료 {article_id} 처리 중 오류: {str(e)}")
                    result["errors"] += 1

            logger.info(f"강의자료 크롤링 완료 - 총: {result['count']}, 신규: {result['new']}, 오류: {result['errors']}")
            return result

        except Exception as e:
            logger.error(f"강의자료 크롤링 중 오류 발생: {str(e)}")
            result["errors"] += 1
            return result

    async def _crawl_assignments(self, user_id: str, course_id: str, assignment_url: str,
                                 auto_download: bool) -> Dict[str, Any]:
        """
        과제 크롤링

        Args:
            user_id: 사용자 ID
            course_id: 강의 ID
            assignment_url: 과제 URL
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
            assignment_repo = SupabaseAssignmentRepository()
            attachment_repo = SupabaseAttachmentRepository()

            existing_assignments = await assignment_repo.get_by_course_id(course_id)
            existing_assignment_ids = {assignment.get('assignment_id') for assignment in existing_assignments if assignment.get('assignment_id')}

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
                    created_assignment = await assignment_repo.create(**assignment)
                    result["new"] += 1

                    # 첨부파일 메타데이터 처리 (항상 실행)
                    if "attachments" in assignment and assignment["attachments"]:
                        logger.debug(f"과제 첨부파일 메타데이터 처리: {len(assignment['attachments'])}개")
                        
                        # 실제 파일 다운로드는 auto_download가 True일 때만
                        if auto_download:
                            attachment_results = await self.file_handler.download_attachments(
                                self.session, assignment, course_id
                            )

                            # 첨부파일 정보 저장
                            for attachment in attachment_results:
                                if attachment["success"]:
                                    attachment_data = {
                                        "file_name": attachment["file_name"],
                                        "original_url": attachment["original_url"],
                                        "storage_path": attachment.get("storage_path", ""),
                                        "source_id": str(created_assignment.get('id', 'unknown')),
                                        "source_type": "assignments",
                                        "course_id": course_id,
                                        "user_id": user_id,
                                    }
                                    await attachment_repo.create(**attachment_data)
                        else:
                            # auto_download=False인 경우에도 첨부파일 메타데이터만 저장
                            for attachment in assignment["attachments"]:
                                try:
                                    attachment_data = {
                                        "file_name": attachment.get("name", "Unknown"),
                                        "original_url": attachment.get("url", ""),
                                        "storage_path": "",
                                        "source_id": str(created_assignment.get('id', 'unknown')),
                                        "source_type": "assignments",
                                        "course_id": course_id,
                                        "user_id": user_id,
                                    }
                                    await attachment_repo.create(**attachment_data)
                                except Exception as e:
                                    logger.error(f"과제 첨부파일 메타데이터 저장 실패: {str(e)}")

                except Exception as e:
                    logger.error(f"과제 {assignment_id} 처리 중 오류: {e}")
                    result["errors"] += 1

            return result

        except Exception as e:
            logger.error(f"과제 크롤링 중 오류 발생: {e}")
            result["errors"] += 1
            return result

    async def crawl_all_courses(self, user_id: str, auto_download: bool = False, is_jwt_user: bool = False) -> Dict[str, Any]:
        """
        모든 강의 크롤링

        Args:
            user_id: 사용자 ID
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
        courses = await self.get_courses(user_id, force_refresh=True, is_jwt_user=is_jwt_user)

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
            self._crawl_all_courses_task(user_id, courses, task_id, auto_download, is_jwt_user)
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
            "courses": [course.get('course_name', course.get('name', 'Unknown')) if course else 'Unknown' for course in courses]
        }

    async def get_notices(self, user_id: str, course_id: str, is_jwt_user: bool = False) -> List[Dict[str, Any]]:
        """
        특정 강의의 공지사항 조회

        Args:
            user_id: 사용자 ID
            course_id: 강의 ID

        Returns:
            List[Dict[str, Any]]: 공지사항 목록
        """
        logger.info(f"사용자 {user_id}의 강의 {course_id} 공지사항 조회")

        # 레포지토리 초기화
        notice_repo = SupabaseNoticeRepository(use_service_key=is_jwt_user)
        attachment_repo = SupabaseAttachmentRepository(use_service_key=is_jwt_user)

        # 저장된 공지사항 가져오기
        notices = await notice_repo.get_by_course_id(course_id)

        # 공지사항 정보와 첨부파일 정보 조합
        result = []
        for notice in notices:
            # notice가 이미 dict 타입이므로 to_dict() 호출 불필요
            notice_dict = notice if isinstance(notice, dict) else notice.to_dict()

            # 첨부파일 조회
            attachments = await attachment_repo.get_by_source(str(notice['id']), "notices")
            notice_dict["attachments"] = attachments

            result.append(notice_dict)

        logger.info(f"강의 {course_id}의 공지사항 {len(result)}개 반환")
        return result

    async def get_materials(self, user_id: str, course_id: str, is_jwt_user: bool = False) -> List[Dict[str, Any]]:
        """
        특정 강의의 강의자료 조회

        Args:
            user_id: 사용자 ID
            course_id: 강의 ID

        Returns:
            List[Dict[str, Any]]: 강의자료 목록
        """
        logger.info(f"사용자 {user_id}의 강의 {course_id} 강의자료 조회")

        # 레포지토리 초기화
        material_repo = SupabaseMaterialRepository(use_service_key=is_jwt_user)
        attachment_repo = SupabaseAttachmentRepository(use_service_key=is_jwt_user)

        # 저장된 강의자료 가져오기
        materials = await material_repo.get_by_course_id(course_id)

        # 강의자료 정보와 첨부파일 정보 조합
        result = []
        for material in materials:
            # material이 이미 dict 타입이므로 to_dict() 호출 불필요
            material_dict = material if isinstance(material, dict) else material.to_dict()

            # 첨부파일 조회
            attachments = await attachment_repo.get_by_source(str(material['id']), "lecture_materials")
            material_dict["attachments"] = attachments

            result.append(material_dict)

        logger.info(f"강의 {course_id}의 강의자료 {len(result)}개 반환")
        return result

    async def get_assignments(self, user_id: str, course_id: str, is_jwt_user: bool = False) -> List[Dict[str, Any]]:
        """
        특정 강의의 과제 조회

        Args:
            user_id: 사용자 ID
            course_id: 강의 ID

        Returns:
            List[Dict[str, Any]]: 과제 목록
        """
        logger.info(f"사용자 {user_id}의 강의 {course_id} 과제 조회")

        # 레포지토리 초기화
        assignment_repo = SupabaseAssignmentRepository(use_service_key=is_jwt_user)
        attachment_repo = SupabaseAttachmentRepository(use_service_key=is_jwt_user)

        # 저장된 과제 가져오기
        assignments = await assignment_repo.get_by_course_id(course_id)

        # 과제 정보와 첨부파일 정보 조합
        result = []
        for assignment in assignments:
            # assignment가 이미 dict 타입이므로 to_dict() 호출 불필요
            assignment_dict = assignment if isinstance(assignment, dict) else assignment.to_dict()

            # 첨부파일 조회
            attachments = await attachment_repo.get_by_source(str(assignment['id']), "assignments")
            assignment_dict["attachments"] = attachments

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

    async def _crawl_all_courses_task(self, user_id: str, courses: List[Dict[str, Any]], task_id: str,
                                      auto_download: bool = False, is_jwt_user: bool = False) -> Dict[str, Any]:
        """
        모든 강의 크롤링 작업 수행

        Args:
            user_id: 사용자 ID
            courses: 강의 목록
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
                    if not course:
                        continue

                    # 실제 eClass 강의 ID 사용 (course_id 필드)
                    course_id = course.get('course_id')
                    if not course_id:
                        continue

                    # 개별 강의 크롤링
                    course_result = await self._crawl_course_task(
                        user_id, course_id, auto_download, f"{task_id}_{course_id}", is_jwt_user
                    )

                    # 결과 저장
                    result["course_results"][course_id] = {
                        "name": course.get('course_name', course.get('name', 'Unknown')),
                        "code": course.get('code', 'Unknown'),
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
                    # course_id가 정의되지 않은 경우를 대비
                    error_course_id = course.get('course_id', 'unknown')
                    logger.error(f"강의 {error_course_id} 크롤링 중 오류: {e}")
                    result["course_results"][error_course_id] = {
                        "name": course.get('course_name', course.get('name', 'Unknown')),
                        "code": course.get('code', 'Unknown'),
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

    async def _crawl_syllabus(self, user_id: str, course_id: str, syllabus_url: str) -> Dict[str, Any]:
        """
        강의계획서 크롤링
        
        Args:
            user_id: 사용자 ID
            course_id: 강의 ID
            syllabus_url: 강의계획서 URL
            
        Returns:
            Dict[str, Any]: 강의계획서 크롤링 결과
        """
        result = {"count": 0, "new": 0, "errors": 0}
        
        try:
            logger.info(f"강의 {course_id}의 강의계획서 크롤링 시작")
            
            # 강의계획서 URL 구성
            base_url = "https://eclass.seoultech.ac.kr"
            if not syllabus_url.startswith("http"):
                syllabus_url = f"{base_url}{syllabus_url}"
            
            # 강의계획서 페이지 요청
            response = await self.session.get(syllabus_url)
            if not response:
                logger.error("강의계획서 페이지 요청 실패")
                result["errors"] += 1
                return result
            
            # 강의계획서 파싱
            syllabus_data = self.parser.parse_syllabus(response.text)
            if not syllabus_data:
                logger.warning(f"강의 {course_id}의 강의계획서가 비어있습니다.")
                return result
            
            result["count"] = 1
            
            # 기존 강의계획서 조회
            syllabus_repo = SupabaseSyllabusRepository()
            existing_syllabus = await syllabus_repo.get_by_course_and_user(course_id, user_id)
            
            # 강의계획서 데이터 준비 (syllabus_id 필드 제거)
            syllabus_save_data = {
                'user_id': user_id,
                'course_id': course_id,
                'basic_info': syllabus_data.get('수업기본정보', {}),
                'instructor_info': syllabus_data.get('담당교수정보', {}),
                'course_plan': syllabus_data.get('강의계획', {}),
                'weekly_plan': syllabus_data.get('주별강의계획', [])
            }
            
            try:
                if existing_syllabus:
                    # 기존 강의계획서 업데이트
                    existing_id = existing_syllabus[0]['id']
                    updated_syllabus = await syllabus_repo.update(existing_id, **syllabus_save_data)
                    if updated_syllabus:
                        logger.info(f"강의계획서 업데이트 완료: {course_id}")
                    else:
                        logger.error(f"강의계획서 업데이트 실패: {course_id}")
                        result["errors"] += 1
                else:
                    # 새 강의계획서 생성
                    created_syllabus = await syllabus_repo.create(**syllabus_save_data)
                    if created_syllabus:
                        result["new"] += 1
                        logger.info(f"새 강의계획서 저장 완료: {course_id}")
                    else:
                        logger.error(f"강의계획서 저장 실패: {course_id}")
                        result["errors"] += 1
                        
            except Exception as e:
                logger.error(f"강의계획서 저장 중 오류: {str(e)}")
                result["errors"] += 1
            
            logger.info(f"강의계획서 크롤링 완료 - 총: {result['count']}, 신규: {result['new']}, 오류: {result['errors']}")
            return result
            
        except Exception as e:
            logger.error(f"강의계획서 크롤링 중 오류 발생: {str(e)}")
            result["errors"] += 1
            return result

    async def get_syllabus(self, user_id: str, course_id: str) -> Dict[str, Any]:
        """
        강의계획서 조회

        Args:
            user_id: 사용자 ID
            course_id: 강의 ID

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
