import pytest
import pytest_asyncio
import httpx
from unittest.mock import Mock, AsyncMock

from app.services.eclass_session import EclassSession


@pytest.mark.asyncio
class TestEclassSession:
    """EclassSession 테스트"""

    @pytest_asyncio.fixture
    async def session(self):
        """EclassSession 인스턴스 생성"""
        session = EclassSession()
        # 테스트 후 리소스 정리
        yield session
        await session.close()

    @pytest_asyncio.fixture
    async def mock_session(self, mocker):
        """Mock HTTP 클라이언트를 사용하는 EclassSession 인스턴스 생성"""
        # AsyncMock을 사용하여 httpx.AsyncClient 모의 구현
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        
        # get과 post 메서드를 AsyncMock으로 설정
        mock_client.get = AsyncMock()
        mock_client.post = AsyncMock()
        
        # EclassSession 인스턴스 생성
        session = EclassSession()
        # 모의 클라이언트로 교체
        session.client = mock_client
        
        # 테스트 후 리소스 정리
        yield session
        await session.close()

    async def test_login_success(self, mock_session):
        """로그인 성공 테스트"""
        # 로그인 성공 응답 모의
        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.text = "document.location.href='main_form.acl'"
        mock_session.client.post.return_value = mock_response
        
        # 로그인 수행
        result = await mock_session.login("testuser", "testpass")
        
        # 검증
        assert result is True
        assert mock_session.user_id == "testuser"
        mock_session.client.post.assert_called_once_with(
            mock_session.login_url,
            data={
                "usr_id": "testuser",
                "usr_pwd": "testpass",
                "returnURL": "",
            }
        )

    async def test_login_failure(self, mock_session):
        """로그인 실패 테스트"""
        # 로그인 실패 응답 모의
        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.text = "로그인 정보가 일치하지 않습니다."
        mock_session.client.post.return_value = mock_response
        
        # 로그인 수행
        result = await mock_session.login("testuser", "wrongpass")
        
        # 검증
        assert result is False
        assert mock_session.user_id is None

    async def test_login_error(self, mock_session):
        """로그인 오류 테스트"""
        # HTTP 오류 모의
        mock_session.client.post.side_effect = httpx.HTTPError("Connection error")
        
        # 로그인 수행
        result = await mock_session.login("testuser", "testpass")
        
        # 검증
        assert result is False
        assert mock_session.user_id is None

    async def test_is_logged_in_true(self, mock_session):
        """로그인 상태 확인 테스트 (로그인됨)"""
        # 사용자 ID 설정
        mock_session.user_id = "testuser"
        
        # 로그인 상태 응답 모의
        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.text = "<html><body>로그아웃</body></html>"
        mock_session.client.get.return_value = mock_response
        
        # 로그인 상태 확인
        result = await mock_session.is_logged_in()
        
        # 검증
        assert result is True
        mock_session.client.get.assert_called_once_with(mock_session.main_url)

    async def test_is_logged_in_false(self, mock_session):
        """로그인 상태 확인 테스트 (로그아웃됨)"""
        # 사용자 ID가 없는 상태
        mock_session.user_id = None
        
        # 로그인 상태 확인
        result = await mock_session.is_logged_in()
        
        # 검증
        assert result is False
        # user_id가 없으면 HTTP 요청을 하지 않아야 함
        mock_session.client.get.assert_not_called()

    async def test_get_request(self, mock_session):
        """GET 요청 테스트"""
        # GET 응답 모의
        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test Content</body></html>"
        mock_session.client.get.return_value = mock_response
        
        # GET 요청 수행
        test_url = "https://eclass.seoultech.ac.kr/test_url"
        test_params = {"param1": "value1", "param2": "value2"}
        response = await mock_session.get(test_url, test_params)
        
        # 검증
        assert response == mock_response
        mock_session.client.get.assert_called_once_with(test_url, params=test_params)

    async def test_post_request(self, mock_session):
        """POST 요청 테스트"""
        # POST 응답 모의
        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test Response</body></html>"
        mock_session.client.post.return_value = mock_response
        
        # POST 요청 수행
        test_url = "https://eclass.seoultech.ac.kr/test_post_url"
        test_data = {"data1": "value1", "data2": "value2"}
        response = await mock_session.post(test_url, test_data)
        
        # 검증
        assert response == mock_response
        mock_session.client.post.assert_called_once_with(test_url, data=test_data)

    async def test_get_course_list(self, mock_session):
        """강의 목록 가져오기 테스트"""
        # 강의 목록 응답 모의
        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.text = "<html><body>Course List</body></html>"
        mock_session.client.get.return_value = mock_response
        
        # 강의 목록 요청
        html = await mock_session.get_course_list()
        
        # 검증
        assert html == mock_response.text
        mock_session.client.get.assert_called_once_with(mock_session.main_url)

    async def test_access_course(self, mock_session):
        """강의실 접근 테스트"""
        # 강의실 접근 응답 모의 (JSON 응답)
        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "isError": False,
            "returnURL": "/ilos/st/course/submain_form.acl?KJKEY=testcourse"
        }
        mock_session.client.post.return_value = mock_response
        
        # 강의실 접근 요청
        course_id = "testcourse"
        return_url = await mock_session.access_course(course_id)
        
        # 검증
        assert return_url == "/ilos/st/course/submain_form.acl?KJKEY=testcourse"
        mock_session.client.post.assert_called_once()
        # 요청 데이터 검증
        call_args = mock_session.client.post.call_args[1]
        assert call_args["data"]["KJKEY"] == course_id

    async def test_access_course_error(self, mock_session):
        """강의실 접근 오류 테스트"""
        # 강의실 접근 오류 응답 모의
        mock_response = AsyncMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "isError": True,
            "message": "접근 권한이 없습니다."
        }
        mock_session.client.post.return_value = mock_response
        
        # 강의실 접근 요청
        course_id = "wrongcourse"
        return_url = await mock_session.access_course(course_id)
        
        # 검증
        assert return_url is None
        mock_session.client.post.assert_called_once()

    async def test_close(self, mock_session):
        """세션 종료 테스트"""
        # 세션 종료
        await mock_session.close()
        
        # 검증
        mock_session.client.aclose.assert_called_once()
