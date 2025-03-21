from typing import List, Dict, Any
import re
import logging
from bs4 import BeautifulSoup
from app.services.parsers.content_parser import ContentParser

logger = logging.getLogger(__name__)

class MaterialParser(ContentParser):
    """강의자료 파싱 클래스"""
    
    def parse_list(self, html: str) -> List[Dict[str, Any]]:
        """강의자료 목록 페이지 파싱"""
        try:
            if not html:
                return []
                
            soup = BeautifulSoup(html, 'html.parser')
            material_rows = soup.select('tr[style*="cursor: pointer"]')
            
            if not material_rows:
                logger.warning("강의자료 목록을 찾을 수 없습니다.")
                return []
                
            materials = []
            for row in material_rows:
                try:
                    # 공지 글은 건너뛰기
                    if row.get('class') and any(cls in ['gongji', 'notitop'] for cls in row.get('class')):
                        continue
                        
                    # 제목 열 찾기
                    title_cell = row.select_one('td.left')
                    if not title_cell:
                        continue
                        
                    # URL 및 article_id 추출
                    onclick = title_cell.get('onclick', '')
                    detail_url = ''
                    article_id = None
                    
                    if onclick:
                        detail_url = self.extract_url_from_onclick(onclick)
                        article_id = self.extract_article_id(detail_url)
                        
                    if not article_id or not detail_url:
                        logger.warning(f"URL 또는 article_id 추출 실패: {onclick}")
                        continue
                        
                    # 제목 추출
                    title_div = title_cell.select_one('.subjt_top')
                    title = title_div.get_text(strip=True) if title_div else ""
                    
                    # 작성자 추출
                    author = ""
                    subjt_bottom = title_cell.select_one('.subjt_bottom')
                    if subjt_bottom:
                        author_span = subjt_bottom.select_one('span')
                        if author_span:
                            author = author_span.get_text(strip=True)
                            
                    # 날짜 추출
                    date_cell = row.select_one('td.number:last-child')
                    date = date_cell.get_text(strip=True) if date_cell else ""
                    
                    # 조회수 추출
                    views = "0"
                    if subjt_bottom:
                        spans = subjt_bottom.find_all('span')
                        if len(spans) > 1:
                            views_text = spans[-1].get_text(strip=True)
                            views_match = re.search(r'\d+', views_text)
                            if views_match:
                                views = views_match.group()
                    
                    # 첨부파일 아이콘 확인
                    download_icons = row.select('img.download_icon')
                    has_attachment = len(download_icons) > 0
                    
                    material = {
                        'article_id': article_id,
                        'title': title,
                        'author': author,
                        'date': date,
                        'views': int(views) if views.isdigit() else 0,
                        'url': detail_url,
                        'has_attachment': has_attachment
                    }
                    materials.append(material)
                    
                except Exception as e:
                    logger.error(f"강의자료 행 파싱 중 오류: {str(e)}")
                    continue
                    
            return materials
            
        except Exception as e:
            logger.error(f"강의자료 목록 파싱 중 오류 발생: {e}")
            return []
    
    def parse_detail(self, html: str) -> Dict[str, Any]:
        """강의자료 상세 페이지 파싱"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            parsed_data = {}
            
            # 본문 내용 추출
            content_element = soup.select_one('td.textviewer')
            if content_element:
                parsed_data['content'] = content_element.get_text(strip=True)
                parsed_data['content_html'] = str(content_element)
                
            # 기본 첨부파일 추출 (페이지에 있는 경우)
            attachments = self.parse_attachments(html)
            if attachments:
                parsed_data['attachments'] = attachments
                
            # 영상 URL 추출 (HTML5 비디오 또는 iframe)
            video_url = ""
            video_elem = soup.select_one('video source')
            if video_elem and 'src' in video_elem.attrs:
                video_url = video_elem['src']
            else:
                iframe_elem = soup.select_one('iframe')
                if iframe_elem and 'src' in iframe_elem.attrs:
                    video_url = iframe_elem['src']
                    
            if video_url:
                parsed_data['video_url'] = video_url
                
            return parsed_data
            
        except Exception as e:
            logger.error(f"강의자료 상세 정보 파싱 중 오류: {str(e)}")
            return {}
