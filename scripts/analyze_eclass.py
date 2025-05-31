#!/usr/bin/env python3
"""
eClass 페이지 구조 상세 분석
"""
import asyncio
import logging
from app.core.config import settings
from app.services.eclass_service import EclassService
from app.services.file_handler import FileHandler
from bs4 import BeautifulSoup
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def analyze_eclass_structure():
    """eClass 페이지 구조 분석"""
    try:
        logger.info("=== eClass 페이지 구조 분석 ===")
        
        # eClass 로그인
        file_handler = FileHandler()
        eclass_service = EclassService(file_handler=file_handler)
        await eclass_service.login(settings.ECLASS_USERNAME, settings.ECLASS_PASSWORD)
        
        # 첫 번째 강의 분석
        course_id = "A2025114608241001"  # Capstone Design I
        logger.info(f"🔍 강의 {course_id} 상세 분석...")
        
        async with httpx.AsyncClient() as client:
            cookies = {}
            if hasattr(eclass_service, 'session'):
                cookies = eclass_service.session.cookies
            
            # 1. 메인 강의 페이지
            main_url = f"https://eclass.seoultech.ac.kr/ilos/st/course/submain_form.acl?KJKEY={course_id}&"
            response = await client.get(main_url, cookies=cookies)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                logger.info("📋 메인 페이지 링크들 분석:")
                all_links = soup.find_all('a', href=True)
                
                # 링크 분류
                lesson_links = []
                material_links = []
                notice_links = []
                
                for link in all_links:
                    href = link.get('href')
                    text = link.get_text(strip=True)
                    
                    if href and text:
                        if 'lesson' in href:
                            lesson_links.append({'text': text, 'href': href})
                        elif 'material' in href or 'data' in href:
                            material_links.append({'text': text, 'href': href})
                        elif 'notice' in href:
                            notice_links.append({'text': text, 'href': href})
                
                logger.info(f"  📚 Lesson 링크: {len(lesson_links)}개")
                for i, link in enumerate(lesson_links[:5]):  # 처음 5개만 표시
                    logger.info(f"    {i+1}. {link['text']} -> {link['href']}")
                
                logger.info(f"  📄 Material 링크: {len(material_links)}개")
                for i, link in enumerate(material_links[:5]):
                    logger.info(f"    {i+1}. {link['text']} -> {link['href']}")
                
                logger.info(f"  📢 Notice 링크: {len(notice_links)}개")
                for i, link in enumerate(notice_links[:5]):
                    logger.info(f"    {i+1}. {link['text']} -> {link['href']}")
                
                # 2. 강의자료실 페이지 확인
                logger.info("\n📁 강의자료실 페이지 확인...")
                data_url = f"https://eclass.seoultech.ac.kr/ilos/st/course/data_list.acl?KJKEY={course_id}&"
                
                data_response = await client.get(data_url, cookies=cookies)
                if data_response.status_code == 200:
                    data_soup = BeautifulSoup(data_response.text, 'html.parser')
                    
                    # 테이블에서 자료 찾기
                    tables = data_soup.find_all('table')
                    logger.info(f"  테이블 수: {len(tables)}")
                    
                    for i, table in enumerate(tables):
                        rows = table.find_all('tr')
                        if len(rows) > 1:  # 헤더가 있는 테이블
                            logger.info(f"  테이블 {i+1}: {len(rows)}개 행")
                            
                            for j, row in enumerate(rows[:3]):  # 처음 3개 행만 확인
                                cells = row.find_all(['td', 'th'])
                                if cells:
                                    cell_texts = [cell.get_text(strip=True) for cell in cells]
                                    logger.info(f"    행 {j+1}: {cell_texts}")
                                    
                                    # 첨부파일 링크 확인
                                    links_in_row = row.find_all('a', href=True)
                                    for link in links_in_row:
                                        href = link.get('href')
                                        if href and ('download' in href or 'attach' in href):
                                            logger.info(f"      🔗 다운로드 링크: {href}")
                
                # 3. 공지사항 페이지 확인
                logger.info("\n📢 공지사항 페이지 확인...")
                notice_url = f"https://eclass.seoultech.ac.kr/ilos/st/course/notice_list.acl?KJKEY={course_id}&"
                
                notice_response = await client.get(notice_url, cookies=cookies)
                if notice_response.status_code == 200:
                    notice_soup = BeautifulSoup(notice_response.text, 'html.parser')
                    
                    # 공지사항 링크들 확인
                    notice_detail_links = notice_soup.find_all('a', href=True)
                    detail_links = []
                    
                    for link in notice_detail_links:
                        href = link.get('href')
                        text = link.get_text(strip=True)
                        if href and 'notice_detail' in href and text:
                            detail_links.append({'text': text, 'href': href})
                    
                    logger.info(f"  📝 공지사항 상세 링크: {len(detail_links)}개")
                    
                    # 첫 번째 공지사항 상세 확인
                    if detail_links:
                        first_notice = detail_links[0]
                        logger.info(f"  첫 번째 공지사항: {first_notice['text']}")
                        
                        detail_url = f"https://eclass.seoultech.ac.kr{first_notice['href']}"
                        detail_response = await client.get(detail_url, cookies=cookies)
                        
                        if detail_response.status_code == 200:
                            detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                            
                            # 첨부파일 확인
                            attach_links = detail_soup.find_all('a', href=True)
                            for link in attach_links:
                                href = link.get('href')
                                text = link.get_text(strip=True)
                                if href and ('attach' in href or 'download' in href or 'file' in href):
                                    logger.info(f"    📎 첨부파일 발견: {text} -> {href}")
                
        logger.info("\n✅ 페이지 구조 분석 완료")
        
    except Exception as e:
        logger.error(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(analyze_eclass_structure())
