import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
from datetime import datetime

from app.services.eclass_service import EclassService
from app.services.eclass_session import EclassSession
from app.services.eclass_parser import EclassParser
from app.services.file_handler import FileHandler


@pytest.mark.asyncio
class TestEclassService:
    """EclassService 테스트"""

    @pytest_asyncio.fixture
    async def mock_session(self):
        """모의 EclassSession 생성"""
        mock_session = AsyncMock(spec=EclassSession)
        mock_session.login.return_value = True
        mock_session.is_logged_in.return_value = True
        mock_session.get_course_list.return_value = "<html>Course List</html>"
        mock_session.access_course.return_value = "/path/to/course"
        
        # GET과 POST 메서드 모의
        mock_response = AsyncMock()
        mock_response.text = "<html>Mock Response</html>"
        mock_response.status_code = 200
        mock_session.get.return_value = mock_response
        mock_session.post.return_value = mock_response
        
        return mock_session

    @pytest_asyncio.fixture
    async def mock_parser(self):
        """모의 EclassParser 생성"""
        mock_parser = MagicMock(spec=EclassParser)
        
        # 강의 목록 파싱 결과 모의
        mock_parser.parse_courses.return_value = [
            {
                "id": "KJ12345",
                "name": "컴퓨터공학개론",
                "code": "CS101",
                "time": "월 10:00-11:30"
            },
            {
                "id": "KJ67890",
                "name": "자료구조",
                "code": "CS201",
                "time": "화 13:00-14:30"
            }
        ]
        
        # 강의 메뉴 파싱 결과 모의
        mock_parser.parse_course_menus.return_value = {
            "notice": {"name": "공지사항", "url": "/path/to/notice"},
            "lecture_material": {"name": "강의자료", "url": "/path/to/material"},
            "assignment": {"name": "과제", "url": "/path/to/assignment"}
        }
        
        # 공지사항 파싱 결과 모의
        mock_parser.parse_notice_list.return_value = [
            {
                "number": "1",
                "article_id": "N12345",
                "title": "중간고사 안내",
                "author": "홍길동 교수",
                "date": "2023-01-10",
                "url": "https://eclass.seoultech.ac.kr/path/to/notice/N12345"
            }
        ]
        mock_parser.parse_notice_detail.return_value = {
            "content": "중간고사는 10월 15일에 실시합니다.",
            "attachments": []
        }
        
        # 강의자료 파싱 결과 모의
        mock_parser.parse_material_list.return_value = [
            {
                "article_id": "M12345",
                "title": "1장 강의자료",
                "author": "홍길동 교수",
                "date": "2023-01-05",
                "url": "https://eclass.seoultech.ac.kr/path/to/material/M12345",
                "has_attachment": True
            }
        ]
        mock_parser.parse_material_detail.return_value = {
            "content": "1장 강의자료입니다.",
            "attachments": [
                {
                    "name": "chapter1.pdf",
                    "url": "https://eclass.seoultech.ac.kr/download/chapter1.pdf"
                }
            ]
        }
        
        # 과제 파싱 결과 모의
        mock_parser.parse_assignment_list.return_value = [
            {
                "assignment_id": "A12345",
                "title": "과제 1",
                "start_date": "2023-01-05",
                "end_date": "2023-01-12",
                "status": "진행중",
                "url": "https://eclass.seoultech.ac.kr/path/to/assignment/A12345"
            }
        ]
        mock_parser.parse_assignment_detail.return_value = {
            "content": "첫 번째 과제입니다.",
            "attachments": []
        }
        
        return mock_parser

    @pytest_asyncio.fixture
    async def mock_file_handler(self):
        """모의 FileHandler 생성"""
        mock_file_handler = AsyncMock(spec=FileHandler)
        
        # 첨부파일 다운로드 결과 모의
        mock_file_handler.download_attachments.return_value = [
            {
                "name": "chapter1.pdf",
                "original_url": "https://eclass.seoultech.ac.kr/download/chapter1.pdf",
                "local_path": "/path/to/download/chapter1.pdf",
                "storage_url": "https://supabase.storage/chapter1.pdf",
                "success": True,
                "timestamp": "2023-01-10T10:00:00"
            }
        ]
        
        return mock_file_handler

    @pytest_asyncio.fixture
    async def mock_db_session(self):
        """모의 데이터베이스 세션 생성"""
        return MagicMock()

    @pytest_asyncio.fixture
    async def service(self, mock_session, mock_parser, mock_file_handler):
        """EclassService 인스턴스 생성"""
        return EclassService(
            session=mock_session,
            parser=mock_parser,
            file_handler=mock_file_handler
        )

    async def test_login(self, service, mock_session):
        """로그인 테스트"""
        # 로그인 수행
        result = await service.login("testuser", "testpass")
        
        # 검증
        assert result is True
        mock_session.login.assert_called_once_with("testuser", "testpass")

    async def test_is_logged_in(self, service, mock_session):
        """로그인 상태 확인 테스트"""
        # 상태 확인
        result = await service.is_logged_in()
        
        # 검증
        assert result is True
        mock_session.is_logged_in.assert_called_once()

    @patch('app.services.eclass_service.CourseRepository')
    async def test_get_courses_from_db(self, MockCourseRepo, service, mock_session, mock_db_session):
        """저장된 강의 목록 조회 테스트"""
        # 모의 레포지토리 설정
        mock_repo = AsyncMock()
        mock_repo.get_by_user_id.return_value = [
            MagicMock(
                eclass_id="KJ12345",
                user_id="testuser",
                name="컴퓨터공학개론",
                code="CS101",
                time="월 10:00-11:30",
                to_dict=lambda: {
                    "id": "KJ12345",
                    "user_id": "testuser",
                    "name": "컴퓨터공학개론",
                    "code": "CS101",
                    "time": "월 10:00-11:30"
                }
            )
        ]
        MockCourseRepo.return_value = mock_repo
        
        # 강의 목록 조회
        courses = await service.get_courses("testuser", mock_db_session, force_refresh=False)
        
        # 검증
        assert len(courses) == 1
        assert courses[0]["id"] == "KJ12345"
        mock_repo.get_by_user_id.assert_called_once_with("testuser")
        # 강제 새로고침이 아니므로 e-Class에서 가져오지 않아야 함
        mock_session.get_course_list.assert_not_called()

    @patch('app.services.eclass_service.CourseRepository')
    async def test_get_courses_refresh(self, MockCourseRepo, service, mock_session, mock_parser, mock_db_session):
        """강의 목록 새로고침 테스트"""
        # 모의 레포지토리 설정
        mock_repo = AsyncMock()
        mock_repo.get_by_user_id.return_value = []
        mock_repo.create.side_effect = lambda data: MagicMock(to_dict=lambda: data)
        MockCourseRepo.return_value = mock_repo
        
        # 강의 목록 새로고침
        courses = await service.get_courses("testuser", mock_db_session, force_refresh=True)
        
        # 검증
        assert len(courses) == 2
        assert courses[0]["id"] == "KJ12345"
        assert courses[1]["id"] == "KJ67890"
        mock_session.get_course_list.assert_called_once()
        mock_parser.parse_courses.assert_called_once()
        assert mock_repo.create.call_count == 2

    @patch('app.services.eclass_service.uuid.uuid4')
    @patch('app.services.eclass_service.asyncio.create_task')
    async def test_crawl_course(self, mock_create_task, mock_uuid4, service, mock_session, mock_db_session):
        """강의 크롤링 테스트"""
        # UUID 모의
        mock_uuid4.return_value.hex = "abcdef12"
        
        # 작업 생성 모의
        mock_task = AsyncMock()
        mock_create_task.return_value = mock_task
        
        # 강의 크롤링 시작
        result = await service.crawl_course("testuser", "KJ12345", mock_db_session)
        
        # 검증
        assert result["task_id"] == "crawl_KJ12345_abcdef12"
        assert result["status"] == "running"
        assert result["course_id"] == "KJ12345"
        mock_create_task.assert_called_once()
        
        # 작업 관리 검증
        assert service.active_tasks["crawl_KJ12345_abcdef12"]["task"] == mock_task
        assert service.active_tasks["crawl_KJ12345_abcdef12"]["status"] == "running"
        assert "start_time" in service.active_tasks["crawl_KJ12345_abcdef12"]

    @patch('app.services.eclass_service.NoticeRepository')
    @patch('app.services.eclass_service.MaterialRepository')
    @patch('app.services.eclass_service.AssignmentRepository')
    @patch('app.services.eclass_service.AttachmentRepository')
    async def test_crawl_course_task(self, MockAttachmentRepo, MockAssignmentRepo, MockMaterialRepo, MockNoticeRepo, 
                                     service, mock_session, mock_parser, mock_file_handler, mock_db_session):
        """강의 크롤링 작업 수행 테스트"""
        # 모의 레포지토리 설정
        mock_notice_repo = AsyncMock()
        mock_notice_repo.get_by_course_id.return_value = []
        mock_notice_repo.create.side_effect = lambda data: MagicMock(id=1, to_dict=lambda: data)
        MockNoticeRepo.return_value = mock_notice_repo
        
        mock_material_repo = AsyncMock()
        mock_material_repo.get_by_course_id.return_value = []
        mock_material_repo.create.side_effect = lambda data: MagicMock(id=1, to_dict=lambda: data)
        MockMaterialRepo.return_value = mock_material_repo
        
        mock_assignment_repo = AsyncMock()
        mock_assignment_repo.get_by_course_id.return_value = []
        mock_assignment_repo.create.side_effect = lambda data: MagicMock(id=1, to_dict=lambda: data)
        MockAssignmentRepo.return_value = mock_assignment_repo
        
        mock_attachment_repo = AsyncMock()
        mock_attachment_repo.create.side_effect = lambda data: MagicMock(id=1, to_dict=lambda: data)
        MockAttachmentRepo.return_value = mock_attachment_repo
        
        # 강의 크롤링 작업 수행
        result = await service._crawl_course_task("testuser", "KJ12345", mock_db_session, True, "test_task_id")
        
        # 검증
        assert result["status"] == "success"
        assert result["course_id"] == "KJ12345"
        assert result["user_id"] == "testuser"
        assert "details" in result
        assert "notices" in result["details"]
        assert "materials" in result["details"]
        assert "assignments" in result["details"]
        
        # 각 컴포넌트 호출 검증
        mock_session.access_course.assert_called_once_with("KJ12345")
        mock_session.get.assert_any_call('/path/to/course')
        mock_parser.parse_course_menus.assert_called_once()
        mock_parser.parse_notice_list.assert_called_once()
        mock_parser.parse_material_list.assert_called_once()
        mock_parser.parse_assignment_list.assert_called_once()
        assert mock_notice_repo.create.call_count == 1
        assert mock_material_repo.create.call_count == 1
        assert mock_assignment_repo.create.call_count == 1
        
        # 첨부파일 처리 검증
        assert mock_file_handler.download_attachments.call_count == 1
        assert mock_attachment_repo.create.call_count == 1

    @patch('app.services.eclass_service.NoticeRepository')
    @patch('app.services.eclass_service.AttachmentRepository')
    async def test_get_notices(self, MockAttachmentRepo, MockNoticeRepo, service, mock_db_session):
        """공지사항 조회 테스트"""
        # 모의 공지사항 레포지토리 설정
        mock_notice = MagicMock()
        mock_notice.id = 1
        mock_notice.article_id = "N12345"
        mock_notice.to_dict.return_value = {
            "id": 1,
            "article_id": "N12345",
            "title": "중간고사 안내",
            "content": "중간고사는 10월 15일에 실시합니다.",
            "author": "홍길동 교수",
            "date": "2023-01-10",
            "course_id": "KJ12345",
            "user_id": "testuser"
        }
        
        mock_notice_repo = AsyncMock()
        mock_notice_repo.get_by_course_id.return_value = [mock_notice]
        MockNoticeRepo.return_value = mock_notice_repo
        
        # 모의 첨부파일 레포지토리 설정
        mock_attachment = MagicMock()
        mock_attachment.id = 1
        mock_attachment.to_dict.return_value = {
            "id": 1,
            "name": "exam_info.pdf",
            "storage_url": "https://supabase.storage/exam_info.pdf",
            "source_id": 1,
            "source_type": "notices"
        }
        
        mock_attachment_repo = AsyncMock()
        mock_attachment_repo.get_by_source.return_value = [mock_attachment]
        MockAttachmentRepo.return_value = mock_attachment_repo
        
        # 공지사항 조회
        notices = await service.get_notices("testuser", "KJ12345", mock_db_session)
        
        # 검증
        assert len(notices) == 1
        assert notices[0]["article_id"] == "N12345"
        assert notices[0]["title"] == "중간고사 안내"
        assert "attachments" in notices[0]
        assert len(notices[0]["attachments"]) == 1
        assert notices[0]["attachments"][0]["name"] == "exam_info.pdf"
        
        mock_notice_repo.get_by_course_id.assert_called_once_with("KJ12345")
        mock_attachment_repo.get_by_source.assert_called_once_with(1, "notices")

    @patch('app.services.eclass_service.MaterialRepository')
    @patch('app.services.eclass_service.AttachmentRepository')
    async def test_get_materials(self, MockAttachmentRepo, MockMaterialRepo, service, mock_db_session):
        """강의자료 조회 테스트"""
        # 모의 강의자료 레포지토리 설정
        mock_material = MagicMock()
        mock_material.id = 1
        mock_material.article_id = "M12345"
        mock_material.to_dict.return_value = {
            "id": 1,
            "article_id": "M12345",
            "title": "1장 강의자료",
            "content": "1장 강의자료입니다.",
            "author": "홍길동 교수",
            "date": "2023-01-05",
            "course_id": "KJ12345",
            "user_id": "testuser"
        }
        
        mock_material_repo = AsyncMock()
        mock_material_repo.get_by_course_id.return_value = [mock_material]
        MockMaterialRepo.return_value = mock_material_repo
        
        # 모의 첨부파일 레포지토리 설정
        mock_attachment = MagicMock()
        mock_attachment.id = 2
        mock_attachment.to_dict.return_value = {
            "id": 2,
            "name": "chapter1.pdf",
            "storage_url": "https://supabase.storage/chapter1.pdf",
            "source_id": 1,
            "source_type": "lecture_materials"
        }
        
        mock_attachment_repo = AsyncMock()
        mock_attachment_repo.get_by_source.return_value = [mock_attachment]
        MockAttachmentRepo.return_value = mock_attachment_repo
        
        # 강의자료 조회
        materials = await service.get_materials("testuser", "KJ12345", mock_db_session)
        
        # 검증
        assert len(materials) == 1
        assert materials[0]["article_id"] == "M12345"
        assert materials[0]["title"] == "1장 강의자료"
        assert "attachments" in materials[0]
        assert len(materials[0]["attachments"]) == 1
        assert materials[0]["attachments"][0]["name"] == "chapter1.pdf"
        
        mock_material_repo.get_by_course_id.assert_called_once_with("KJ12345")
        mock_attachment_repo.get_by_source.assert_called_once_with(1, "lecture_materials")

    @patch('app.services.eclass_service.AssignmentRepository')
    @patch('app.services.eclass_service.AttachmentRepository')
    async def test_get_assignments(self, MockAttachmentRepo, MockAssignmentRepo, service, mock_db_session):
        """과제 조회 테스트"""
        # 모의 과제 레포지토리 설정
        mock_assignment = MagicMock()
        mock_assignment.id = 1
        mock_assignment.assignment_id = "A12345"
        mock_assignment.to_dict.return_value = {
            "id": 1,
            "assignment_id": "A12345",
            "title": "과제 1",
            "content": "첫 번째 과제입니다.",
            "start_date": "2023-01-05",
            "end_date": "2023-01-12",
            "status": "진행중",
            "course_id": "KJ12345",
            "user_id": "testuser"
        }
        
        mock_assignment_repo = AsyncMock()
        mock_assignment_repo.get_by_course_id.return_value = [mock_assignment]
        MockAssignmentRepo.return_value = mock_assignment_repo
        
        # 모의 첨부파일 레포지토리 설정
        mock_attachment_repo = AsyncMock()
        mock_attachment_repo.get_by_source.return_value = []
        MockAttachmentRepo.return_value = mock_attachment_repo
        
        # 과제 조회
        assignments = await service.get_assignments("testuser", "KJ12345", mock_db_session)
        
        # 검증
        assert len(assignments) == 1
        assert assignments[0]["assignment_id"] == "A12345"
        assert assignments[0]["title"] == "과제 1"
        assert "attachments" in assignments[0]
        assert len(assignments[0]["attachments"]) == 0
        
        mock_assignment_repo.get_by_course_id.assert_called_once_with("KJ12345")
        mock_attachment_repo.get_by_source.assert_called_once_with(1, "assignments")

    async def test_get_task_status(self, service):
        """작업 상태 조회 테스트"""
        # 테스트 작업 추가
        task_id = "test_task_id"
        service.active_tasks[task_id] = {
            "status": "completed",
            "start_time": "2023-01-01T10:00:00",
            "end_time": "2023-01-01T10:05:00",
            "result": {"status": "success"}
        }
        
        # 작업 상태 조회
        status = await service.get_task_status(task_id)
        
        # 검증
        assert status["task_id"] == task_id
        assert status["status"] == "completed"
        assert status["start_time"] == "2023-01-01T10:00:00"
        assert status["end_time"] == "2023-01-01T10:05:00"
        assert "result" in status

    async def test_get_task_status_not_found(self, service):
        """존재하지 않는 작업 상태 조회 테스트"""
        # 존재하지 않는 작업 ID
        task_id = "non_existent_task"
        
        # 작업 상태 조회
        status = await service.get_task_status(task_id)
        
        # 검증
        assert status["task_id"] == task_id
        assert status["status"] == "not_found"

    async def test_cancel_task(self, service):
        """작업 취소 테스트"""
        # 모의 작업 추가
        task_id = "cancel_test_task"
        mock_task = AsyncMock()
        mock_task.done.return_value = False
        mock_task.cancel = AsyncMock()  # cancel을 별도로 모의
        
        service.active_tasks[task_id] = {
            "task": mock_task,
            "status": "running",
            "start_time": "2023-01-01T10:00:00"
        }
        
        # 작업 취소
        result = await service.cancel_task(task_id)
        
        # 검증
        assert result is True
        assert service.active_tasks[task_id]["status"] == "canceled"
        assert "end_time" in service.active_tasks[task_id]
        mock_task.cancel.assert_called_once()

    async def test_cancel_task_not_found(self, service):
        """존재하지 않는 작업 취소 테스트"""
        # 존재하지 않는 작업 ID
        task_id = "non_existent_task"
        
        # 작업 취소
        result = await service.cancel_task(task_id)
        
        # 검증
        assert result is False

    async def test_close(self, service, mock_session):
        """서비스 종료 테스트"""
        # 모의 작업 추가
        task_id = "running_task"
        mock_task = AsyncMock()
        mock_task.done.return_value = False
        
        service.active_tasks[task_id] = {
            "task": mock_task,
            "status": "running",
            "start_time": "2023-01-01T10:00:00"
        }
        
        # 서비스 종료
        await service.close()
        
        # 검증
        assert service.active_tasks[task_id]["status"] == "canceled"
        assert "end_time" in service.active_tasks[task_id]
        mock_task.cancel.assert_called_once()
        mock_session.close.assert_called_once()
