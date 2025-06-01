#!/usr/bin/env python3
"""
강의 메뉴에서 강의계획서 링크 찾기
"""
import asyncio
import sys
import os
sys.path.append('/Users/elaus/PycharmProjects/AutoLMS-R')

from app.services.eclass_session import EclassSession
from app.services.eclass_parser import EclassParser
from app.core.config import settings

async def find_syllabus_in_menu():
    """강의 메뉴에서 강의계획서 링크 찾기"""
    print("🔍 강의 메뉴에서 강의계획서 링크 찾기")
    
    session = EclassSession()
    parser = EclassParser()
    
    try:
        # 1. 로그인
        print("🔐 eClass 로그인 중...")
        login_success = await session.login(settings.ECLASS_USERNAME, settings.ECLASS_PASSWORD)
        if not login_success:
            print("❌ 로그인 실패")
            return
        print("✅ 로그인 성공")
        
        # 2. 강의 목록 가져오기
        print("📚 강의 목록 조회 중...")
        course_html = await session.get_course_list()
        courses = parser.parse_courses(course_html)
        
        if not courses:
            print("❌ 강의가 없습니다")
            return
            
        course = courses[0]
        course_id = course['id']
        print(f"🎯 선택된 강의: {course['name']} ({course_id})")
        
        # 3. 강의실 접근
        print("🚪 강의실 접근 중...")
        course_url = await session.access_course(course_id)
        if not course_url:
            print("❌ 강의실 접근 실패")
            return
        print(f"✅ 강의실 URL: {course_url}")
        
        # 4. 강의 메뉴 페이지 가져오기
        print("📋 강의 메뉴 페이지 요청 중...")
        response = await session.get(course_url)
        
        if not response:
            print("❌ 강의 메뉴 페이지 응답 없음")
            return
            
        html_content = response.text
        print(f"✅ 강의 메뉴 페이지 응답 받음 (길이: {len(html_content)})")
        
        # 5. HTML 파일로 저장
        os.makedirs("debug_html", exist_ok=True)
        html_file_path = f"debug_html/course_menu_{course_id}.html"
        with open(html_file_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"💾 강의 메뉴 HTML 저장: {html_file_path}")
        
        # 6. 강의계획서 관련 링크 찾기
        print("🔍 강의계획서 관련 링크 찾기...")
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 모든 링크 찾기
        links = soup.find_all('a', href=True)
        syllabus_links = []
        
        for link in links:
            href = link['href']
            text = link.text.strip()
            
            # 강의계획서 관련 키워드 검색
            syllabus_keywords = ['강의계획', 'syllabus', 'course_info', '계획서', 'plan']
            if any(keyword in href.lower() or keyword in text.lower() for keyword in syllabus_keywords):
                syllabus_links.append({
                    'text': text,
                    'href': href
                })
                print(f"  📋 발견: '{text}' -> {href}")
        
        if not syllabus_links:
            print("❌ 강의계획서 링크를 찾을 수 없습니다")
            
            # 모든 링크 출력 (디버깅용)
            print("🔍 모든 링크 목록:")
            for i, link in enumerate(links[:20]):  # 처음 20개만
                print(f"  {i+1}. '{link.text.strip()}' -> {link['href']}")
        else:
            print(f"✅ 강의계획서 링크 {len(syllabus_links)}개 발견")
            
            # 첫 번째 링크로 테스트
            first_link = syllabus_links[0]
            test_url = first_link['href']
            
            # 상대 경로면 절대 경로로 변환
            if not test_url.startswith('http'):
                base_url = "https://eclass.seoultech.ac.kr"
                test_url = f"{base_url}{test_url}"
            
            print(f"🧪 첫 번째 링크 테스트: {test_url}")
            
            # 링크 접근 시도
            test_response = await session.get(test_url)
            if test_response:
                print(f"✅ 링크 접근 성공 (길이: {len(test_response.text)})")
                
                # 테스트 HTML 저장
                test_html_path = f"debug_html/syllabus_test_{course_id}.html"
                with open(test_html_path, "w", encoding="utf-8") as f:
                    f.write(test_response.text)
                print(f"💾 테스트 HTML 저장: {test_html_path}")
            else:
                print("❌ 링크 접근 실패")
        
        # 7. 강의 메뉴 파싱도 테스트
        print("🔧 강의 메뉴 파싱 테스트...")
        course_menus = parser.parse_course_menus(html_content)
        print(f"📋 파싱된 메뉴: {list(course_menus.keys())}")
        
        # plan 메뉴가 있는지 확인
        if "plan" in course_menus:
            plan_menu = course_menus["plan"]
            print(f"📋 Plan 메뉴 발견: {plan_menu}")
            
            # Plan 메뉴 접근 시도
            plan_url = plan_menu["url"]
            if not plan_url.startswith('http'):
                plan_url = f"https://eclass.seoultech.ac.kr{plan_url}"
            
            print(f"🧪 Plan 메뉴 접근: {plan_url}")
            plan_response = await session.get(plan_url)
            
            if plan_response:
                print(f"✅ Plan 메뉴 접근 성공 (길이: {len(plan_response.text)})")
                
                # Plan HTML 저장
                plan_html_path = f"debug_html/plan_{course_id}.html"
                with open(plan_html_path, "w", encoding="utf-8") as f:
                    f.write(plan_response.text)
                print(f"💾 Plan HTML 저장: {plan_html_path}")
            else:
                print("❌ Plan 메뉴 접근 실패")
        
        # 8. 세션 종료
        await session.close()
        print("🚪 세션 종료")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(find_syllabus_in_menu())
