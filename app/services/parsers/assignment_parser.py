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
                
            # HTML 길이 확인
            logger.debug(f"과제 HTML 응답 길이: {len(html)} 바이트")
                
            soup = BeautifulSoup(html, 'html.parser')
            # 과제 테이블 찾기 (실제 HTML 구조에 맞게 수정)
            assignment_table = soup.find('table', class_='bbslist new_bbslist')
            if not assignment_table:
                # 대안: 부분 클래스 매칭 시도
                assignment_table = soup.find('table', class_=lambda x: x and 'bbslist' in x)
            
            if not assignment_table:
                logger.warning("과제 테이블을 찾을 수 없습니다.")
                return []
                
            # 과제 행 찾기 (tbody 내부 tr 사용)
            tbody = assignment_table.find('tbody')
            if tbody:
                assignment_rows = tbody.find_all('tr')
            else:
                # 대안: 헤더를 제외한 모든 tr
                assignment_rows = assignment_table.find_all('tr')[1:]
            
            assignments = []
            for row in assignment_rows:
                try:
                    cols = row.find_all('td')
                    if len(cols) < 8:  # 실제 과제 행은 8개의 열을 가짐
                        continue
                        
                    # onclick 속성에서 URL 추출 (실제 HTML: pageMove('/ilos/st/course/report_view_form.acl?RT_SEQ=...'))
                    onclick_value = row.get('onclick', '')
                    if not onclick_value:
                        # td 내부에서 onclick 속성을 가진 요소 찾기
                        onclick_td = row.find('td', attrs={'onclick': True})
                        if onclick_td:
                            onclick_value = onclick_td.get('onclick', '')
                    
                    detail_url = self.extract_url_from_onclick(onclick_value)
                    
                    # 과제 ID 추출 (RT_SEQ 파라미터 사용)
                    assignment_id = None
                    if detail_url and 'RT_SEQ=' in detail_url:
                        import re
                        match = re.search(r'RT_SEQ=(\d+)', detail_url)
                        if match:
                            assignment_id = match.group(1)
                    
                    if not assignment_id:
                        assignment_id = self.extract_article_id(detail_url)
                    
                    if not assignment_id or not detail_url:
                        continue
                        
                    # 제목 추출 (div.subjt_top에서 실제 제목 추출)
                    title = cols[2].text.strip()
                    subjt_top = cols[2].find('div', class_='subjt_top')
                    if subjt_top:
                        title = subjt_top.text.strip()
                    
                    assignment = {
                        'assignment_id': assignment_id,
                        'title': title,
                        'progress_status': cols[3].text.strip(),  # 진행 상태
                        'submission_status': cols[4].text.strip(),  # 제출 상태  
                        'score': cols[5].text.strip(),  # 점수
                        'max_score': cols[6].text.strip(),  # 배점
                        'due_date': cols[7].text.strip(),  # 마감일
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
