from typing import List, Dict, Any
import re
import logging
from bs4 import BeautifulSoup
from app.services.parsers.content_parser import ContentParser

logger = logging.getLogger(__name__)

class NoticeParser(ContentParser):
    """공지사항 파싱 클래스"""
    
    def parse_list(self, html: str) -> List[Dict[str, Any]]:
        """공지사항 목록 페이지 파싱"""
        try:
            if not html:
                return []
                
            # 임시 디버그 로깅 - HTML 내용 확인
            logger.warning(f"[DEBUG] HTML 응답 길이: {len(html)} 바이트")
            logger.warning(f"[DEBUG] HTML 응답 내용 샘플: {html[:500]}...")
            if len(html) <= 400:  # 짧은 응답이면 전체 내용 출력
                logger.warning(f"[DEBUG] HTML 전체 내용: {html}")
                
            soup = BeautifulSoup(html, 'html.parser')
            logger.info("공지사항 HTML 파싱 시작")

            notice_rows = soup.find_all('tr', style="cursor: pointer;")
            logger.info(f"발견된 공지사항 행 수: {len(notice_rows)}")

            if not notice_rows:
                logger.warning("공지사항 목록을 찾을 수 없습니다.")
                # 대안 셀렉터로 시도
                alternative_rows = soup.find_all('tr')
                logger.warning(f"[DEBUG] 전체 tr 태그 수: {len(alternative_rows)}")
                return []

            notices = []
            for row in notice_rows:
                try:
                    # onclick 속성에서 URL과 article_id 추출
                    onclick = row.select_one('td.left').get('onclick', '')
                    article_id = None
                    detail_url = ''

                    if onclick:
                        detail_url = self.extract_url_from_onclick(onclick)
                        article_id = self.extract_article_id(detail_url)

                    if not article_id or not detail_url:
                        continue

                    cols = row.find_all('td')
                    if len(cols) >= 5:
                        title_element = cols[2].find('div', class_='subjt_top')
                        title = title_element.get_text(strip=True) if title_element else ''

                        # 작성자 및 조회수 추출
                        bottom_div = cols[2].find('div', class_='subjt_bottom')
                        author = ''
                        views = ''

                        if bottom_div:
                            spans = bottom_div.find_all('span')
                            if spans:
                                author = spans[0].get_text(strip=True)
                                if len(spans) > 1:
                                    views_text = spans[-1].get_text(strip=True)
                                    views_match = re.search(r'\d+', views_text)
                                    if views_match:
                                        views = views_match.group()

                        notice = {
                            'number': cols[0].text.strip(),
                            'article_id': article_id,
                            'title': title,
                            'author': author,
                            'date': cols[4].text.strip(),
                            'views': int(views) if views.isdigit() else 0,
                            'url': detail_url
                        }
                        notices.append(notice)

                except Exception as e:
                    logger.error(f"공지사항 행 파싱 중 오류 발생: {e}")
                    continue

            # 최신순으로 정렬
            notices.reverse()
            return notices

        except Exception as e:
            logger.error(f"공지사항 목록 파싱 중 오류 발생: {e}")
            return []
    
    def parse_detail(self, html: str) -> Dict[str, Any]:
        """공지사항 상세 페이지 파싱"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            detail = {}
            
            # 텍스트뷰어 찾기
            textviewer = soup.find('td', class_='textviewer')
            if not textviewer:
                # 다른 방법으로 내용 찾기
                table = soup.find('table', class_='bbsview')
                if table:
                    rows = table.find_all('tr')
                    if rows and len(rows) > 0:
                        textviewer = rows[-1].find('td')

            if textviewer:
                # 내용 추출
                content_div = textviewer.find('div')
                if content_div:
                    # HTML 태그 처리
                    for br in content_div.find_all('br'):
                        br.replace_with('\n')
                    for p in content_div.find_all('p'):
                        p.insert_after(soup.new_string('\n'))
                    detail['content'] = content_div.get_text(strip=True)
                    detail['content_html'] = str(content_div)
                else:
                    # div가 없는 경우 직접 텍스트 추출
                    detail['content'] = textviewer.get_text(strip=True)
                    detail['content_html'] = str(textviewer)

            # 기본 첨부파일 추출 (페이지에 있는 경우)
            attachments = self.parse_attacthments(html)
            if attachments:
                detail['attachments'] = attachments

            return detail
            
        except Exception as e:
            logger.error(f"공지사항 상세 파싱 중 오류 발생: {e}")
            return {}
