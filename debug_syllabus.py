#!/usr/bin/env python3
"""
Syllabus 디버깅 - 실제 HTML 구조 확인
"""
import asyncio
import sys
import os
sys.path.append('/Users/elaus/PycharmProjects/AutoLMS-R')

from app.services.eclass_session import EclassSession
from app.services.eclass_parser import EclassParser
from app.core.config import settings

async def debug_syllabus():
    """Syllabus 페이지 구조 디버깅"""
    print("🔍 Syllabus 디버깅 시작")
    
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
        user_id = session.user_id
        print(f"🎯 선택된 강의: {course['name']} ({course_id})")
        print(f"👤 사용자 ID: {user_id}")
        
        # 3. Syllabus URL 구성
        base_url = "https://eclass.seoultech.ac.kr"
        syllabus_url = f"{base_url}/lecture/course_info.jsp?ref=1&ud={user_id}&ky={course_id}"
        print(f"📋 Syllabus URL: {syllabus_url}")
        
        # 4. Syllabus 페이지 요청
        print("📄 Syllabus 페이지 요청 중...")
        response = await session.get(syllabus_url)
        
        if not response:
            print("❌ Syllabus 페이지 응답 없음")
            return
            
        html_content = response.text
        print(f"✅ Syllabus 페이지 응답 받음 (길이: {len(html_content)})")
        
        # 5. HTML 파일로 저장 (디버깅용)
        os.makedirs("debug_html", exist_ok=True)
        html_file_path = f"debug_html/syllabus_{course_id}.html"
        with open(html_file_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"💾 HTML 파일 저장: {html_file_path}")
        
        # 6. 기본 구조 분석
        print("🔍 HTML 구조 분석 중...")
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 테이블 개수 확인
        tables = soup.find_all('table')
        print(f"📊 테이블 개수: {len(tables)}개")
        
        # 섹션 제목 찾기
        section_divs = soup.find_all('div', style=lambda value: value and 'font-weight: bold' in value)
        print(f"📑 섹션 제목 개수: {len(section_divs)}개")
        
        for i, div in enumerate(section_divs[:5]):  # 처음 5개만
            print(f"  {i+1}. {div.text.strip()}")
        
        # 강의계획서 관련 키워드 검색
        keywords = ['수업기본정보', '담당교수정보', '강의계획', '주별강의계획', '교재', '평가']
        print("🔍 키워드 검색 결과:")
        for keyword in keywords:
            if keyword in html_content:
                print(f"  ✅ '{keyword}' 발견")
            else:
                print(f"  ❌ '{keyword}' 없음")
        
        # 7. 파서로 파싱 시도
        print("🔧 파서로 파싱 시도...")
        syllabus_data = parser.parse_syllabus(html_content)
        print(f"📋 파싱 결과: {syllabus_data}")
        
        if syllabus_data:
            print("✅ 강의계획서 파싱 성공!")
            for section, data in syllabus_data.items():
                print(f"  📂 {section}: {len(data) if isinstance(data, (list, dict)) else 'N/A'}개 항목")
        else:
            print("❌ 강의계획서 파싱 실패")
        
        # 8. 세션 종료
        await session.close()
        print("🚪 세션 종료")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_syllabus())
