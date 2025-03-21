from typing import List, Dict, Any
import re
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class SyllabusParser:
    """강의계획서 파싱 클래스"""
    
    def clean_text(self, text: str) -> str:
        """HTML에서 추출한 텍스트 정리"""
        if not text:
            return ""
        # 공백 문자 정리
        text = re.sub(r'\s+', ' ', text.strip())
        # HTML 엔티티 변환
        text = text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>')
        return text
    
    def parse_syllabus(self, html: str) -> Dict[str, Any]:
        """강의계획서 파싱"""
        try:
            if not html:
                return {}
                
            soup = BeautifulSoup(html, 'html.parser')
            
            # 강의 기본 정보 추출
            syllabus_info = {
                '수업기본정보': {},
                '담당교수정보': {},
                '강의계획': {},
                '주별강의계획': []
            }
            
            # 섹션 제목 찾기
            sections = soup.find_all('div',
                                    style=lambda value: value and 'padding-top' in value and 'font-weight: bold' in value)
            
            for section in sections:
                section_title = section.text.strip()
                section_key = None
                
                # 섹션 제목 맵핑
                if '[수업기본정보]' in section_title:
                    section_key = '수업기본정보'
                elif '[담당교수정보]' in section_title:
                    section_key = '담당교수정보'
                elif '[강의계획]' in section_title:
                    section_key = '강의계획'
                elif '[주별강의계획]' in section_title:
                    section_key = '주별강의계획'
                
                if section_key and section_key in syllabus_info:
                    table = section.find_next('table')
                    if table:
                        if section_key != '주별강의계획':
                            self._extract_table_info(table, syllabus_info[section_key])
                        else:
                            self._extract_weekly_syllabus(table, syllabus_info[section_key])
            
            return syllabus_info
            
        except Exception as e:
            logger.error(f"강의계획서 파싱 중 오류 발생: {e}")
            return {}
    
    def _extract_table_info(self, table: BeautifulSoup, info_dict: Dict[str, str]) -> None:
        """테이블 정보 추출"""
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['th', 'td'])
            if len(cells) >= 2:
                key = cells[0].text.strip()
                value = cells[1].text.strip()
                info_dict[key] = value
    
    def _extract_weekly_syllabus(self, table: BeautifulSoup, weekly_syllabus: List[Dict[str, str]]) -> None:
        """주별 강의계획 추출"""
        rows = table.find_all('tr')[1:]  # 헤더 제외
        seen_weeks = set()  # 이미 처리한 주차 추적
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 3:
                week = cols[0].text.strip()
                content = cols[1].text.strip()
                note = cols[2].text.strip()
                
                # 빈 행이거나 이미 처리한 주차라면 건너뜀
                if not (week and content) or week in seen_weeks:
                    continue
                    
                # 주차 기록
                seen_weeks.add(week)
                
                weekly_syllabus.append({
                    '주차': week,
                    '내용': content,
                    '비고': note
                })
