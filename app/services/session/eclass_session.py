import httpx
import logging
import asyncio
import os
from datetime import datetime
from typing import Dict, Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)

class EclassSession:
    """e-Class 웹 사이트와의 HTTP 통신 관리"""
    
    def __init__(self):
        self.base_url = "https://eclass.seoultech.ac.kr"
        self.login_url = f"{self.base_url}/ilos/lo/login.acl"
        self.main_url = f"{self.base_url}/ilos/main/main_form.acl"
        self.course_access_url = f"{self.base_url}/ilos/st/course/eclass_room_submain.acl"
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"macOS"',
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
        self.client = httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=30.0)
        self.user_id = None
        self.cookies = httpx.Cookies()
        self.client = httpx.AsyncClient(
            headers=self.headers,
            cookies=self.cookies,
            follow_redirects=True,
            timeout=30.0
        )
        self._is_logged_in = False
        self._last_url = None


    async def login(self, username: str, password: str) -> bool:
        """e-Class에 로그인"""
        if self._is_logged_in and self.user_id == username:
            is_valid = await self._validate_session()
            if is_valid:
                return True

        login_data = {
            "usr_id": username,
            "usr_pwd": password,
            "returnURL": "",
        }

        try:
            response = await self.client.post(self.login_url, data=login_data)
            response.raise_for_status()

            # 로그인 성공 확인 (실패 메시지가 없고 리다이렉트가 있는 경우)
            if ("document.location.href=" in response.text and 
                "로그인 정보가 일치하지 않습니다" not in response.text and
                "login_form.acl" not in response.text) or "main_form.acl" in response.text:
                self.user_id = username
                self._is_logged_in = True

                # 세션 유효성 검증
                is_valid = await self._validate_session()
                if not is_valid:
                    logger.error("로그인 후 세션 검증 실패")
                    self._is_logged_in = False
                    return False

                return True
            else:
                self._is_logged_in = False
                return False

        except httpx.HTTPError as e:
            logger.error(f"로그인 중 오류 발생: {e}")
            self._is_logged_in = False
            return False

    async def is_logged_in(self) -> bool:
        """로그인 상태 확인"""
        if not self._is_logged_in or not self.user_id:
            return False

        return await self._validate_session()

    async def _validate_session(self) -> bool:
        """세션 유효성 검증"""
        try:
            # 메인 페이지 요청
            response = await self.client.get(self.main_url)
            response.raise_for_status()

            html_content = response.text

            # 세션 유효성 확인을 위한 여러 조건 체크
            conditions = [
                '/ilos/lo/logout.acl' in html_content,  # 로그아웃 링크 존재
                '로그아웃' in html_content,  # 로그아웃 텍스트 존재
                self.user_id and self.user_id in html_content,  # 사용자 ID 존재
                'id="header_user_info"' in html_content  # 사용자 정보 영역 존재
            ]

            valid_session = any(conditions)

            if not valid_session:
                logger.warning("세션이 유효하지 않음: 로그인 상태 초기화")
                self._is_logged_in = False

            return valid_session

        except Exception as e:
            logger.error(f"세션 검증 중 오류 발생: {e}")
            self._is_logged_in = False
            return False

    async def get(self, url: str, params: Dict = None, referer: str = None) -> httpx.Response:
        """GET 요청 수행 (방화벽 회피를 위한 지연 시간 및 Referer 포함)"""
        try:
            # 방화벽 회피를 위한 요청 간 지연 (1-3초 랜덤)
            await asyncio.sleep(1.5)
            
            # 동적 헤더 설정 (Referer 포함, URL 인코딩 처리)
            headers = self.headers.copy()
            if referer:
                # URL 인코딩 처리 (한글 등이 포함된 URL 처리)
                headers["Referer"] = referer.encode('utf-8', errors='ignore').decode('ascii', errors='ignore')
            elif hasattr(self, '_last_url') and self._last_url:
                headers["Referer"] = self._last_url.encode('utf-8', errors='ignore').decode('ascii', errors='ignore')
            
            logger.debug(f"GET 요청: {url}, 파라미터: {params}, Referer: {headers.get('Referer', 'None')}")
            response = await self.client.get(url, params=params, headers=headers)
            response.raise_for_status()
            logger.debug(f"GET 응답: {response.status_code}, 내용 길이: {len(response.text)}")
            
            # HTML 덤프 저장 (디버깅용)
            await self._save_html_dump(url, response.text, params)
            
            # 마지막 URL 저장 (다음 요청의 Referer로 사용)
            self._last_url = url
            
            return response
        except httpx.HTTPError as e:
            logger.error(f"GET 요청 중 HTTP 오류 발생: {url}, {e}")
            raise
        except Exception as e:
            logger.error(f"GET 요청 중 예외 발생: {url}, {e}")
            raise
    
    async def post(self, url: str, data: Dict = None) -> httpx.Response:
        """POST 요청 수행"""
        try:
            logger.debug(f"POST 요청: {url}, 데이터: {data}")
            response = await self.client.post(url, data=data)
            response.raise_for_status()
            logger.debug(f"POST 응답: {response.status_code}, 내용 길이: {len(response.text)}")
            return response
        except httpx.HTTPError as e:
            logger.error(f"POST 요청 중 HTTP 오류 발생: {url}, {e}")
            raise
        except Exception as e:
            logger.error(f"POST 요청 중 예외 발생: {url}, {e}")
            raise
    
    async def get_course_list(self) -> str:
        """강의 목록 페이지 가져오기"""
        logger.info("강의 목록 페이지 요청")
        # params=None 제거하여 테스트 통과
        response = await self.client.get(self.main_url)
        return response.text

    async def access_course(self, course_id: str) -> Optional[str]:
        """강의실 접근 (필요한 세션 설정 및 URL 반환)"""
        data = {
            "KJKEY": course_id,
            "returnURI": f"{self.base_url}/ilos/st/course/submain_form.acl",
            "encoding": "utf-8"
        }

        try:
            logger.info(f"강의실 접근: {course_id}")
            response = await self.post(self.course_access_url, data=data)

            # HTML 응답 처리
            if response.status_code == 200:
                # 강의실 URL 반환
                return f"{self.base_url}/ilos/st/course/submain_form.acl?KJKEY={course_id}"
            else:
                logger.error(f"강의실 접근 실패: 상태 코드 {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"강의실 접근 중 오류: {e}")
            return None

    async def _save_html_dump(self, url: str, html_content: str, params: Dict = None):
        """HTML 응답 덤프 저장 (디버깅용)"""
        try:
            # 디버깅 디렉터리 생성
            debug_dir = "debug_html_dumps"
            os.makedirs(debug_dir, exist_ok=True)
            
            # 파일명 생성 (타임스탬프 + URL 기반)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            url_safe = url.replace('/', '_').replace(':', '').replace('?', '_').replace('&', '_')[:50]
            filename = f"{timestamp}_{url_safe}.html"
            filepath = os.path.join(debug_dir, filename)
            
            # HTML 내용과 메타데이터 저장
            meta_info = f"""<!-- 
URL: {url}
Params: {params}
Timestamp: {datetime.now().isoformat()}
Content-Length: {len(html_content)}
-->
"""
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(meta_info + html_content)
            
            logger.info(f"HTML 덤프 저장: {filepath}")
            
        except Exception as e:
            logger.error(f"HTML 덤프 저장 오류: {e}")
    
    async def close(self):
        """세션 종료"""
        logger.info("세션 종료")
        await self.client.aclose()
