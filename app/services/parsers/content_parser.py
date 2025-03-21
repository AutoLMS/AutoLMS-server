from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import re
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

class ContentParser(ABC):
    """
    콘텐츠 파싱을 위한 추상 기본 클래스.
    공지사항, 강의자료, 과제 등 콘텐츠 파싱을 위한 공통 메서드를 정의합니다.
    """
    
    def clean_text(self, text: str) -> str:
        """HTML에서 추출한 텍스트 정리"""
        if not text:
            return ""
        # 공백 문자 정리
        text = re.sub(r'\s+', ' ', text.strip())
        # HTML 엔티티 변환
        text = text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>')
        return text
    
    def extract_table_data(self, html: str, selector: str) -> List[Dict[str, Any]]:
        """HTML 테이블에서 데이터 추출"""
        if not html:
            return []
            
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.select_one(selector)
        if not table:
            return []
            
        rows = table.select('tr')
        if not rows:
            return []
            
        # 헤더 추출
        headers = []
        header_row = rows[0]
        for th in header_row.select('th'):
            headers.append(self.clean_text(th.text))
            
        # 데이터 추출
        result = []
        for row in rows[1:]:  # 헤더 행 제외
            cells = row.select('td')
            if not cells:
                continue
                
            row_data = {}
            for i, cell in enumerate(cells):
                if i < len(headers):
                    row_data[headers[i]] = self.clean_text(cell.text)
            
            # 링크 추출 (있는 경우)
            links = row.select('a')
            if links:
                for link in links:
                    if 'href' in link.attrs:
                        row_data['url'] = link['href']
                        break
                        
            result.append(row_data)
            
        return result
    
    def extract_content_seq(self, html: str) -> Optional[str]:
        """CONTENT_SEQ 파라미터 추출"""
        if not html:
            return None
            
        # URL에서 추출 시도
        url_match = re.search(r'CONTENT_SEQ=([^&]+)', html)
        if url_match:
            return url_match.group(1)
            
        # 스크립트에서 추출 시도
        soup = BeautifulSoup(html, 'html.parser')
        for script in soup.find_all('script'):
            if script.string and 'CONTENT_SEQ' in script.string:
                match = re.search(r'CONTENT_SEQ\s*:\s*["\']([^"\',]+)', script.string)
                if match:
                    return match.group(1)
                    
        # hidden input에서 추출 시도
        seq_input = soup.select_one('input[name="CONTENT_SEQ"]')
        if seq_input:
            return seq_input.get('value')
            
        return None
    
    def extract_article_id(self, url: str) -> Optional[str]:
        """URL에서 게시글 ID 추출"""
        if not url:
            return None

        # ARTL_NUM 또는 NORCT_NUM 파라미터 찾기
        for param in ['ARTL_NUM', 'NORCT_NUM']:
            match = re.search(fr'{param}=([\d]+)', url)
            if match:
                return match.group(1)

        return None
    
    def extract_url_from_onclick(self, onclick_value: str) -> str:
        """onclick 속성에서 URL 추출"""
        match = re.search(r"pageMove\('([^']+)'(?:,\s*event)?", onclick_value)
        if match:
            url = match.group(1)
            base_url = "https://eclass.seoultech.ac.kr"
            if not url.startswith('http'):
                url = base_url + url
            return url
        return ""
    
    def parse_attachments(self, html: str) -> List[Dict[str, Any]]:
        """첨부파일 정보 파싱"""
        attachments = []
        
        if not html:
            return attachments
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # 첨부파일 링크 찾기
        for file_link in soup.find_all('a', href=lambda h: h and 'efile_download.acl' in h):
            try:
                file_url = file_link.get('href', '')
                file_name = file_link.text.strip()

                # 상대 URL인 경우 절대 URL로 변환
                if file_url and not file_url.startswith('http'):
                    file_url = f"https://eclass.seoultech.ac.kr{file_url}"

                attachment = {
                    'file_name': file_name,
                    'original_url': file_url
                }
                
                # FILE_SEQ 추출
                file_seq_match = re.search(r'FILE_SEQ=([^&]+)', file_url)
                if file_seq_match:
                    attachment['file_seq'] = file_seq_match.group(1)
                
                attachments.append(attachment)
                logger.debug(f"첨부파일 정보 추출: {attachment}")

            except Exception as e:
                logger.error(f"첨부파일 정보 추출 중 오류: {str(e)}")
                continue
                
        return attachments
    
    async def fetch_attachments_via_ajax(self, eclass_session, content_seq: str, course_id: str) -> List[Dict[str, Any]]:
        """
        AJAX 요청을 통해 첨부파일 목록 가져오기
        
        Args:
            eclass_session: E-Class 세션 객체
            content_seq: 콘텐츠 시퀀스 번호
            course_id: 강의 ID
            
        Returns:
            List[Dict[str, Any]]: 첨부파일 정보 목록
        """
        if not content_seq or not course_id or not eclass_session:
            return []
            
        try:
            # AJAX 요청 URL 및 데이터
            efile_list_url = "https://eclass.seoultech.ac.kr/ilos/co/efile_list.acl"
            form_data = {
                'ky': course_id,
                'pf_st_flag': '2',  # 학생 권한
                'CONTENT_SEQ': content_seq,
                'encoding': 'utf-8'
            }
            
            # AJAX 요청 수행
            response = await eclass_session.post(efile_list_url, data=form_data)
            
            if not response or not response.text:
                logger.error("첨부파일 목록 AJAX 요청 실패")
                return []
                
            # 첨부파일 정보 파싱
            return self.parse_attachments(response.text)
            
        except Exception as e:
            logger.error(f"첨부파일 AJAX 요청 중 오류: {str(e)}")
            return []
    
    @abstractmethod
    def parse_list(self, html: str) -> List[Dict[str, Any]]:
        """콘텐츠 목록 페이지 파싱"""
        pass
    
    @abstractmethod
    def parse_detail(self, html: str) -> Dict[str, Any]:
        """콘텐츠 상세 페이지 파싱"""
        pass
        
    async def parse_detail_with_attachments(self, eclass_session, html: str, course_id: str) -> Dict[str, Any]:
        """
        첨부파일 정보를 포함한 콘텐츠 상세 페이지 파싱
        
        Args:
            eclass_session: E-Class 세션 객체
            html: 파싱할 HTML 내용
            course_id: 강의 ID
            
        Returns:
            Dict[str, Any]: 파싱 결과 (첨부파일 정보 포함)
        """
        try:
            # 기본 상세 정보 파싱
            result = self.parse_detail(html)
            
            # 첨부파일이 이미 파싱되었는지 확인
            if not result.get('attachments') or len(result['attachments']) == 0:
                # CONTENT_SEQ 추출
                content_seq = self.extract_content_seq(html)
                
                if content_seq:
                    # AJAX 요청으로 첨부파일 정보 가져오기
                    attachments = await self.fetch_attachments_via_ajax(
                        eclass_session, content_seq, course_id
                    )
                    
                    if attachments:
                        result['attachments'] = attachments
            
            return result
            
        except Exception as e:
            logger.error(f"첨부파일 정보 포함 상세 파싱 중 오류: {str(e)}")
            # 기본 파싱 결과라도 반환
            return self.parse_detail(html)
