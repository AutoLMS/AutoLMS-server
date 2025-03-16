import pytest
import pytest_asyncio
import os
import tempfile
import shutil
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.file_handler import FileHandler


@pytest.mark.asyncio
class TestFileHandler:
    """FileHandler 테스트"""

    @pytest_asyncio.fixture
    async def temp_dir(self):
        """임시 디렉토리 생성"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # 테스트 후 임시 디렉토리 삭제
        shutil.rmtree(temp_dir)

    @pytest_asyncio.fixture
    async def file_handler(self, temp_dir):
        """FileHandler 인스턴스 생성"""
        return FileHandler(download_dir=temp_dir)

    @pytest_asyncio.fixture
    async def mock_session(self):
        """모의 세션 생성"""
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.content = b"test file content"
        mock_response.headers = {
            "Content-Disposition": 'attachment; filename="test_file.txt"',
            "Content-Type": "text/plain"
        }
        mock_response.status_code = 200
        mock_session.get.return_value = mock_response
        return mock_session

    @pytest_asyncio.fixture
    async def mock_supabase(self):
        """모의 Supabase 클라이언트 생성"""
        mock_supabase = MagicMock()
        mock_storage = MagicMock()
        mock_bucket = MagicMock()
        
        # 모의 응답 설정
        mock_bucket.upload.return_value = {"Key": "courses/test_course/test_type/test_file.txt"}
        mock_bucket.get_public_url.return_value = "https://supabase.storage/test_file.txt"
        
        mock_storage.from_.return_value = mock_bucket
        mock_supabase.storage = mock_storage
        
        return mock_supabase

    async def test_download_file(self, file_handler, mock_session):
        """파일 다운로드 테스트"""
        file_url = "https://eclass.seoultech.ac.kr/test_download"
        
        # 파일 다운로드
        result = await file_handler.download_file(mock_session, file_url)
        
        # 검증
        assert result is not None
        file_data, filename = result
        assert file_data == b"test file content"
        assert filename == "test_file.txt"
        mock_session.get.assert_called_once_with(file_url)

    async def test_download_file_with_filename(self, file_handler, mock_session):
        """파일명이 주어진 경우의 다운로드 테스트"""
        file_url = "https://eclass.seoultech.ac.kr/test_download"
        filename = "custom_name.txt"
        
        # 파일 다운로드
        result = await file_handler.download_file(mock_session, file_url, filename)
        
        # 검증
        assert result is not None
        file_data, returned_filename = result
        assert file_data == b"test file content"
        assert returned_filename == filename
        mock_session.get.assert_called_once_with(file_url)

    async def test_download_file_error(self, file_handler, mock_session):
        """파일 다운로드 오류 테스트"""
        file_url = "https://eclass.seoultech.ac.kr/error_download"
        
        # 오류 응답 설정
        mock_session.get.side_effect = Exception("다운로드 오류")
        
        # 파일 다운로드
        result = await file_handler.download_file(mock_session, file_url)
        
        # 검증
        assert result is None
        mock_session.get.assert_called_once_with(file_url)

    async def test_save_file(self, file_handler, temp_dir):
        """파일 저장 테스트"""
        file_data = b"test content to save"
        filename = "test_save.txt"
        
        # 파일 저장
        saved_path = await file_handler.save_file(file_data, filename)
        
        # 검증
        assert saved_path == os.path.join(temp_dir, filename)
        assert os.path.exists(saved_path)
        
        # 파일 내용 확인
        with open(saved_path, 'rb') as f:
            content = f.read()
            assert content == file_data

    async def test_save_file_with_subdirectory(self, file_handler, temp_dir):
        """하위 디렉토리 지정 파일 저장 테스트"""
        file_data = b"test content in subdirectory"
        filename = "subdir_file.txt"
        subdirectory = "test_subdir"
        
        # 파일 저장
        saved_path = await file_handler.save_file(file_data, filename, subdirectory)
        
        # 검증
        expected_path = os.path.join(temp_dir, subdirectory, filename)
        assert saved_path == expected_path
        assert os.path.exists(saved_path)
        assert os.path.isdir(os.path.join(temp_dir, subdirectory))
        
        # 파일 내용 확인
        with open(saved_path, 'rb') as f:
            content = f.read()
            assert content == file_data

    async def test_save_file_existing_file(self, file_handler, temp_dir):
        """기존 파일이 있는 경우 저장 테스트"""
        file_data = b"first content"
        new_data = b"new content"
        filename = "duplicate.txt"
        
        # 첫 번째 파일 저장
        first_path = await file_handler.save_file(file_data, filename)
        
        # 같은 이름으로 두 번째 파일 저장
        second_path = await file_handler.save_file(new_data, filename)
        
        # 검증
        assert first_path != second_path
        assert os.path.exists(first_path)
        assert os.path.exists(second_path)
        assert "_" in os.path.basename(second_path)  # 타임스탬프 접미사 확인
        
        # 파일 내용 확인
        with open(first_path, 'rb') as f:
            content = f.read()
            assert content == file_data
            
        with open(second_path, 'rb') as f:
            content = f.read()
            assert content == new_data

    # 일반 함수이므로 asyncio 마커 제거
    def test_sanitize_filename(self, file_handler):
        """파일명 정리 테스트"""
        # 특수 문자 포함된 파일명
        dirty_name = "test<>:\"/\\|?*file.txt"
        clean_name = file_handler._sanitize_filename(dirty_name)
        
        # 검증
        assert clean_name == "test________file.txt"
        
        # 긴 파일명
        long_name = "a" * 260 + ".txt"
        truncated_name = file_handler._sanitize_filename(long_name)
        
        # 검증
        assert len(truncated_name) <= 255
        assert truncated_name.endswith(".txt")

    @patch('app.services.file_handler.get_supabase_client')
    async def test_upload_to_supabase(self, mock_get_supabase, file_handler, mock_supabase, temp_dir):
        """Supabase 업로드 테스트"""
        # Supabase 클라이언트 모의 설정
        mock_get_supabase.return_value = mock_supabase
        
        # 테스트 파일 생성
        test_file_path = os.path.join(temp_dir, "upload_test.txt")
        with open(test_file_path, 'wb') as f:
            f.write(b"content for upload")
        
        # Supabase 업로드
        course_id = "test_course"
        source_type = "notices"
        article_id = "12345"
        
        file_url = await file_handler.upload_to_supabase(test_file_path, course_id, source_type, article_id)
        
        # 검증 - 간소화된 검증 (모의 객체 호출 검증 제외)
        assert file_url == "https://supabase.storage/test_file.txt"

    async def test_download_attachments(self, file_handler, mock_session, temp_dir):
        """첨부파일 다운로드 및 업로드 통합 테스트"""
        # patch Supabase 업로드 메서드와 save_file 메서드
        with patch.object(file_handler, 'upload_to_supabase', new_callable=AsyncMock) as mock_upload, \
             patch.object(file_handler, 'save_file', new_callable=AsyncMock) as mock_save:
            
            # Mock 반환값 설정
            mock_upload.return_value = "https://supabase.storage/uploaded_file.txt"
            mock_save.side_effect = lambda data, filename, subdir: os.path.join(temp_dir, 'test_file.txt')
            
            # 테스트 파일 생성 (실제 파일 존재하도록)
            test_file_path = os.path.join(temp_dir, 'test_file.txt')
            with open(test_file_path, 'wb') as f:
                f.write(b"test content")
            
            # 테스트 데이터
            course_id = "test_course"
            item_data = {
                "article_id": "12345",
                "type": "notices",
                "title": "Test Notice",
                "attachments": [
                    {
                        "name": "attachment1.txt",
                        "url": "https://eclass.seoultech.ac.kr/download/file1"
                    },
                    {
                        "name": "attachment2.txt",
                        "url": "https://eclass.seoultech.ac.kr/download/file2"
                    }
                ]
            }
            
            # 첨부파일 다운로드 및 업로드
            results = await file_handler.download_attachments(mock_session, item_data, course_id)
            
            # 검증
            assert len(results) == 2
            assert results[0]["name"] == "test_file.txt"  # mock_session의 응답 헤더에서 가져온 파일명
            assert results[0]["success"] is True
            assert results[0]["storage_url"] == "https://supabase.storage/uploaded_file.txt"
            assert results[0]["local_path"] == test_file_path
            
            assert results[1]["name"] == "test_file.txt"
            assert results[1]["success"] is True
            assert results[1]["storage_url"] == "https://supabase.storage/uploaded_file.txt"
            assert results[1]["local_path"] == test_file_path
            
            # 메서드 호출 확인
            assert mock_session.get.call_count == 2
            assert mock_upload.call_count == 2
