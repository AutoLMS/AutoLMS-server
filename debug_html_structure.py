#!/usr/bin/env python3
"""HTML 구조 확인 스크립트"""

import asyncio
import logging
import os
from app.services.eclass_service import EclassService
from app.core.config import settings

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def debug_html_structure():
    """HTML 구조 확인"""
    service = EclassService()
    
    try:
        # 로그인
        print("로그인 시도...")
        login_success = await service.login(settings.ECLASS_USERNAME, settings.ECLASS_PASSWORD)
        if not login_success:
            print("로그인 실패")
            return
        print("로그인 성공")
        
        # 강의 목록 가져오기
        user_id = 'af56401f-da61-44fb-a201-3bfe163ecee3'
        courses = await service.get_courses(user_id, force_refresh=False)
        
        if courses:
            # 여러 강의 시도
            for i, course in enumerate(courses[:3]):  # 첫 3개 강의만
                if not course:
                    continue
                    
                course_id = course.get('course_id') or course.get('id')
                course_name = course.get('course_name') or course.get('name', 'Unknown')
                print(f"\n=== 강의 {i+1}: {course_name} (ID: {course_id}) ===")
                
                # 강의실 접근
                course_url = await service.session.access_course(course_id)
                if not course_url:
                    print("강의실 접근 실패")
                    continue
                
                # 메뉴 페이지 HTML 저장
                response = await service.session.get(course_url)
                
                # HTML 파일 저장
                html_dir = "debug_html"
                os.makedirs(html_dir, exist_ok=True)
                
                # 메뉴 페이지 저장
                menu_file = os.path.join(html_dir, f"course_{course_id}_menu.html")
                with open(menu_file, "w", encoding="utf-8") as f:
                    f.write(response.text)
                print(f"메뉴 HTML 저장: {menu_file}")
                
                # 메뉴 파싱 결과 확인
                course_menus = service.parser.parse_course_menus(response.text)
                print(f"파싱된 메뉴: {list(course_menus.keys())}")
                
                # 공지사항 페이지 확인
                if "notice" in course_menus:
                    notice_url = f"https://eclass.seoultech.ac.kr{course_menus['notice']['url']}"
                    notice_url = notice_url.replace('notice_list_form', 'notice_list')
                    
                    data = {
                        'start': '1',
                        'display': '10',
                        'SCH_VALUE': '',
                        'ud': service.session.user_id,
                        'ky': course_id,
                        'encoding': 'utf-8'
                    }
                    
                    notice_response = await service.session.post(notice_url, data=data)
                    notice_file = os.path.join(html_dir, f"course_{course_id}_notice.html")
                    with open(notice_file, "w", encoding="utf-8") as f:
                        f.write(notice_response.text)
                    print(f"공지사항 HTML 저장: {notice_file}")
                    
                    # 공지사항 파싱 결과 확인
                    notices = service.parser.parse_notice_list(notice_response.text)
                    print(f"공지사항 수: {len(notices)}")
                
                # 강의자료 페이지 확인  
                if "lecture_material" in course_menus:
                    material_url = f"https://eclass.seoultech.ac.kr{course_menus['lecture_material']['url']}"
                    material_url = material_url.replace('lecture_material_list_form', 'lecture_material_list')
                    
                    material_response = await service.session.get(material_url)
                    material_file = os.path.join(html_dir, f"course_{course_id}_material.html")
                    with open(material_file, "w", encoding="utf-8") as f:
                        f.write(material_response.text)
                    print(f"강의자료 HTML 저장: {material_file}")
                    
                    # 강의자료 파싱 결과 확인
                    materials = service.parser.parse_material_list(material_response.text)
                    print(f"강의자료 수: {len(materials)}")
                
                print("-" * 50)
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await service.close()

if __name__ == "__main__":
    asyncio.run(debug_html_structure())