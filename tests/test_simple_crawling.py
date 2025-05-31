#!/usr/bin/env python3
"""
실제 eClass 크롤링을 테스트하는 스크립트 (간단한 버전)
"""
import asyncio
import sys
import json
import os
from datetime import datetime
sys.path.append('/Users/elaus/PycharmProjects/AutoLMS-R')

from app.services.eclass_session import EclassSession
from app.services.eclass_parser import EclassParser
from app.core.config import settings

async def test_simple_eclass_crawling():
    """간단한 eClass 크롤링 테스트"""
    print("🔄 간단한 eClass 크롤링 테스트 시작...")
    
    try:
        # 세션과 파서 초기화
        session = EclassSession()
        parser = EclassParser()
        
        # 1. 로그인 테스트
        print(f"📧 eClass 로그인 시도: {settings.ECLASS_USERNAME}")
        login_success = await session.login(settings.ECLASS_USERNAME, settings.ECLASS_PASSWORD)
        
        if not login_success:
            print("❌ eClass 로그인 실패")
            return False
        
        print("✅ eClass 로그인 성공!")
        
        # 2. 강의 목록 크롤링 테스트
        print("📚 강의 목록 크롤링 중...")
        course_html = await session.get_course_list()
        
        if not course_html:
            print("❌ 강의 목록을 가져오는데 실패")
            return False
        
        courses = parser.parse_courses(course_html)
        print(f"✅ 강의 {len(courses)}개 발견:")
        for i, course in enumerate(courses[:3]):  # 처음 3개만 출력
            print(f"  {i+1}. {course.get('name', 'Unknown')} ({course.get('id', 'No ID')})")
        
        # 3. 첫 번째 강의의 상세 정보 크롤링
        if courses:
            first_course = courses[0]
            course_id = first_course.get('id')
            course_name = first_course.get('name')
            
            print(f"\n📖 '{course_name}' 강의 상세 크롤링 중...")
            
            # 강의실 접근
            course_url = await session.access_course(course_id)
            if not course_url:
                print(f"❌ 강의실 {course_id} 접근 실패")
                return False
            
            # 강의 메뉴 파싱
            response = await session.get(course_url)
            course_menus = parser.parse_course_menus(response.text)
            
            print(f"📋 강의 메뉴: {list(course_menus.keys())}")
            
            # 공지사항 크롤링 (간단 버전)
            if "notice" in course_menus:
                try:
                    notice_url = f"https://eclass.seoultech.ac.kr{course_menus['notice']['url']}"
                    notice_url = notice_url.replace('notice_list_form', 'notice_list')
                    
                    data = {
                        'start': '1',
                        'display': '10',
                        'SCH_VALUE': '',
                        'ud': session.user_id,
                        'ky': course_id,
                        'encoding': 'utf-8'
                    }
                    
                    notice_response = await session.post(notice_url, data=data)
                    if notice_response:
                        notices = parser.parse_notice_list(notice_response.text)
                        print(f"📢 공지사항: {len(notices)}개")
                    else:
                        print("📢 공지사항: 요청 실패")
                except Exception as e:
                    print(f"📢 공지사항 크롤링 오류: {e}")
            
            # 강의자료 크롤링 (간단 버전)
            if "lecture_material" in course_menus:
                try:
                    material_url = f"https://eclass.seoultech.ac.kr{course_menus['lecture_material']['url']}"
                    material_url = material_url.replace('lecture_material_list_form', 'lecture_material_list')
                    
                    material_response = await session.get(material_url)
                    if material_response:
                        materials = parser.parse_material_list(material_response.text)
                        print(f"📄 강의자료: {len(materials)}개")
                        
                        # 첨부파일 확인
                        attachment_count = 0
                        for material in materials:
                            if material.get('has_attachment', False):
                                attachment_count += 1
                        print(f"📎 첨부파일이 있는 자료: {attachment_count}개")
                    else:
                        print("📄 강의자료: 요청 실패")
                except Exception as e:
                    print(f"📄 강의자료 크롤링 오류: {e}")
            
            # 과제 크롤링 (간단 버전)
            if "assignment" in course_menus:
                try:
                    assignment_url = f"https://eclass.seoultech.ac.kr{course_menus['assignment']['url']}"
                    assignment_response = await session.get(assignment_url)
                    if assignment_response:
                        assignments = parser.parse_assignment_list(assignment_response.text)
                        print(f"📝 과제: {len(assignments)}개")
                    else:
                        print("📝 과제: 요청 실패")
                except Exception as e:
                    print(f"📝 과제 크롤링 오류: {e}")
            
            # 크롤링 결과를 JSON 파일로 저장
            crawl_result = {
                "timestamp": datetime.now().isoformat(),
                "courses_count": len(courses),
                "test_course": {
                    "id": course_id,
                    "name": course_name,
                    "menus": course_menus
                },
                "sample_courses": courses[:3],
                "crawling_success": True
            }
            
            # 결과 저장
            output_file = "test_data/simple_crawl_test_result.json"
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(crawl_result, f, ensure_ascii=False, indent=2)
            
            print(f"💾 크롤링 결과 저장: {output_file}")
        
        # 4. 로그아웃
        await session.close()
        print("🚪 eClass 로그아웃 완료")
        
        return True
        
    except Exception as e:
        print(f"❌ 크롤링 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_simple_eclass_crawling())
    if success:
        print("🎯 간단한 eClass 크롤링 테스트 성공!")
    else:
        print("❌ 간단한 eClass 크롤링 테스트 실패")
