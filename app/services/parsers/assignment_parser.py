from typing import List, Dict, Any
import re
import logging
from bs4 import BeautifulSoup
from app.services.parsers.content_parser import ContentParser

logger = logging.getLogger(__name__)

class AssignmentParser(ContentParser):
    """과제 파싱 클래스"""
    
    def parse_list(self, html: str) -> List[Dict[str, Any]]:
        """과제 목록 페이지 파싱"""
        try:
            if not html:
                return []
                
            soup = BeautifulSoup(html, 'html.parser')
            # 과제 테이블 찾기
            assignment_table = soup.find('table', class_='table_topic')
            if not assignment_table:
                logger.warning("과제 테이블을 찾을 수 없습니다.")
                return []
                
            # 과제 행 찾기
            assignment_rows = assignment_table.find_all('tr')[1:]  # 헤더 제외
            
            assignments = []
            for row in assignment_rows:
                try:
                    cols = row.find_all('td')
                    if len(cols) < 7:  # 과제 행은 보통 7개 이상의 열을 가짐
                        continue
                        
                    # onclick 속성에서 URL 추출
                    onclick_value = row.get('onclick', '')
                    detail_url = self.extract_url_from_onclick(onclick_value)
                    
                    # 과제 ID 추출
                    assignment_id = self.extract_article_id(detail_url)
                    
                    if not assignment_id or not detail_url:
                        continue
                        
                    assignment = {
                        'assignment_id': assignment_id,
                        'title': cols[1].text.strip(),
                        'start_date': cols[3].text.strip(),
                        'end_date': cols[4].text.strip(),
                        'status': cols[5].text.strip(),
                        'url': detail_url
                    }
                    assignments.append(assignment)
                    
                except Exception as e:
                    logger.error(f"과제 행 파싱 중 오류 발생: {str(e)}")
                    continue
                    
            return assignments
            
        except Exception as e:
            logger.error(f"과제 목록 파싱 중 오류 발생: {e}")
            return []
    
    def parse_detail(self, html: str) -> Dict[str, Any]:
        """과제 상세 내용 파싱"""
        try:
            if not html:
                return {}
                
            soup = BeautifulSoup(html, 'html.parser')
            detail = {}
            
            # 과제 테이블 찾기
            assignment_table = soup.find('table', class_='bbsview')
            if assignment_table:
                # 과제 내용 추출
                content_td = assignment_table.find('td', class_='textviewer')
                if content_td:
                    # HTML 태그 처리
                    for br in content_td.find_all('br'):
                        br.replace_with('\n')
                    for p in content_td.find_all('p'):
                        p.insert_after(soup.new_string('\n'))
                    
                    detail['content'] = content_td.get_text(strip=True)
                    detail['content_html'] = str(content_td)
                    
            # 마감일 추출 (상세 페이지에서 다시 확인)
            due_date = ""
            due_date_label = soup.find(string=re.compile('마감일|제출기한'))
            if due_date_label and due_date_label.parent:
                due_date_elem = due_date_label.parent.find_next_sibling()
                if due_date_elem:
                    due_date = self.clean_text(due_date_elem.text)
                    
            # 점수 정보 추출
            score_info = {}
            score_label = soup.find(string=re.compile('배점|점수'))
            if score_label and score_label.parent:
                score_elem = score_label.parent.find_next_sibling()
                if score_elem:
                    score_info['max_score'] = self.clean_text(score_elem.text)
                    
            # 내 점수 정보 추출 (제출한 경우)
            my_score_label = soup.find(string=re.compile('내 점수|획득 점수'))
            if my_score_label and my_score_label.parent:
                my_score_elem = my_score_label.parent.find_next_sibling()
                if my_score_elem:
                    score_info['my_score'] = self.clean_text(my_score_elem.text)
                    
            # 기본 첨부파일 추출 (페이지에 있는 경우)
            attachments = self.parse_attachments(html)
            
            # 결과 취합
            if due_date:
                detail['due_date'] = due_date
                
            if score_info:
                detail['score_info'] = score_info
                
            if attachments:
                detail['attachments'] = attachments
                
            return detail
            
        except Exception as e:
            logger.error(f"과제 상세 파싱 중 오류 발생: {e}")
            return {}
