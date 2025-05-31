#!/usr/bin/env python3
"""
eClass에서 실제 첨부파일이 있는 강의자료 찾기
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

async def find_materials_with_attachments():
    """첨부파일이 있는 강의자료 찾기"""
    try:
        logger.info("=== 첨부파일이 있는 강의자료 찾기 ===")
        
        # eClass 로그인
        file_handler = FileHandler()
        eclass_service = EclassService(file_handler=file_handler)
        await eclass_service.login(settings.ECLASS_USERNAME, settings.ECLASS_PASSWORD)
        
        # 테스트할 강의 목록
        test_courses = [
            "A2025114608241001",  # Capstone Design I
            "A2025114608541001",  # IT Project Management
            "A2025114607141001",  # Information Security
            "A2025114608341001",  # Strategic Technology Management
            "A2025114610241001",  # UX Analytics
        ]
        
        found_attachments = []
        
        for course_id in test_courses:
            logger.info(f"\n🔍 강의 {course_id} 확인 중...")
            
            # 강의자료 페이지 접근
            materials_url = f"https://eclass.seoultech.ac.kr/ilos/st/course/submain_form.acl?KJKEY={course_id}&"
            
            async with httpx.AsyncClient() as client:
                # eClass 세션 사용
                cookies = {}
                if hasattr(eclass_service, 'session'):
                    cookies = eclass_service.session.cookies
                
                response = await client.get(materials_url, cookies=cookies)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 강의자료 링크들 찾기
                    material_links = soup.find_all('a', href=True)
                    
                    for link in material_links:
                        href = link.get('href')
                        if href and 'st/course/lesson_detail_form.acl' in href:
                            material_title = link.get_text(strip=True)
                            if material_title:
                                logger.info(f"  📄 발견: {material_title}")
                                
                                # 각 강의자료의 상세 페이지 확인
                                detail_url = f"https://eclass.seoultech.ac.kr{href}"
                                detail_response = await client.get(detail_url, cookies=cookies)
                                
                                if detail_response.status_code == 200:
                                    detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                                    
                                    # 첨부파일 링크 확인
                                    attachment_links = detail_soup.find_all('a', href=True)
                                    for att_link in attachment_links:
                                        att_href = att_link.get('href')
                                        if att_href and ('download' in att_href.lower() or 'file' in att_href.lower() or '.pdf' in att_href.lower() or '.docx' in att_href.lower()):
                                            file_name = att_link.get_text(strip=True)
                                            if file_name and not file_name.startswith('http'):
                                                found_attachments.append({
                                                    'course_id': course_id,
                                                    'material_title': material_title,
                                                    'file_name': file_name,
                                                    'download_url': f"https://eclass.seoultech.ac.kr{att_href}",
                                                    'detail_url': detail_url
                                                })
                                                logger.info(f"    📎 첨부파일 발견: {file_name}")
                
                await asyncio.sleep(1)  # 요청 간격 조절
        
        logger.info(f"\n📊 총 {len(found_attachments)}개의 첨부파일 발견")
        
        for i, attachment in enumerate(found_attachments):
            logger.info(f"{i+1}. {attachment['course_id']} - {attachment['material_title']}")
            logger.info(f"   파일: {attachment['file_name']}")
            logger.info(f"   URL: {attachment['download_url']}")
        
        return found_attachments
        
    except Exception as e:
        logger.error(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    asyncio.run(find_materials_with_attachments())
