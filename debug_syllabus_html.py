#!/usr/bin/env python3

"""
강의계획서 HTML 구조 분석 및 디버깅
"""

import asyncio
from app.services.auth_service import AuthService
from app.services.eclass_service import EclassService

async def debug_syllabus_html():
    """강의계획서 HTML 구조 분석"""
    try:
        # 기존 로그인된 사용자 ID 사용
        user_id = "7eb9befa-2833-456b-b857-08d71b226fe5"
        
        # AuthService로 자격증명 가져오기
        auth_service = AuthService()
        eclass_credentials = await auth_service.get_user_eclass_credentials(user_id)
        
        # eClass 서비스 로그인
        eclass_service = EclassService()
        await eclass_service.login(
            eclass_credentials["eclass_username"], 
            eclass_credentials["eclass_password"]
        )
        
        # 강의계획서 URL 구성
        course_id = "A2025310911441009"
        base_url = "https://eclass.seoultech.ac.kr"
        syllabus_url = f"{base_url}/lecture/course_info.jsp?ref=1&ud={user_id}&ky={course_id}"
        
        print(f"🔗 강의계획서 URL: {syllabus_url}")
        
        # 직접 HTML 요청
        response = await eclass_service.session.get(syllabus_url)
        if not response:
            print("❌ 강의계획서 페이지 요청 실패")
            return False
        
        html_content = response.text
        print(f"📄 HTML 길이: {len(html_content)} 문자")
        
        # HTML 구조 분석
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        print("\n🔍 HTML 구조 분석:")
        print("-" * 50)
        
        # 테이블 찾기
        tables = soup.find_all('table')
        print(f"📊 테이블 개수: {len(tables)}")
        
        # div 태그 찾기 (섹션 제목용)
        divs_with_style = soup.find_all('div', style=True)
        print(f"🎨 스타일 있는 div 개수: {len(divs_with_style)}")
        
        # 섹션 제목 후보 찾기
        section_candidates = []
        for div in divs_with_style:
            text = div.text.strip()
            if any(keyword in text for keyword in ['수업기본정보', '담당교수정보', '강의계획', '주별강의계획']):
                section_candidates.append((text, div.get('style', '')))
        
        print(f"📝 섹션 제목 후보: {len(section_candidates)}개")
        for text, style in section_candidates:
            print(f"   - '{text}' (스타일: {style[:100]}...)")
        
        # 전체 텍스트에서 키워드 검색
        full_text = soup.get_text()
        keywords = ['수업기본정보', '담당교수정보', '강의계획', '주별강의계획', '강의명', '교수명']
        
        print(f"\n🔎 키워드 검색 결과:")
        for keyword in keywords:
            if keyword in full_text:
                print(f"   ✅ '{keyword}' 발견")
            else:
                print(f"   ❌ '{keyword}' 없음")
        
        # HTML 샘플 저장
        sample_length = 2000
        print(f"\n📄 HTML 샘플 (처음 {sample_length}자):")
        print("=" * 60)
        print(html_content[:sample_length])
        print("=" * 60)
        
        # 파서 테스트
        print(f"\n🧪 현재 파서 테스트:")
        parsed_result = eclass_service.parser.parse_syllabus(html_content)
        print(f"파싱 결과 키: {list(parsed_result.keys())}")
        print(f"각 섹션 데이터 존재 여부:")
        for key, value in parsed_result.items():
            if isinstance(value, dict):
                print(f"   - {key}: {len(value)}개 항목")
            elif isinstance(value, list):
                print(f"   - {key}: {len(value)}개 항목")
            else:
                print(f"   - {key}: {type(value)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 디버깅 실패: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    result = asyncio.run(debug_syllabus_html())
    print("\n" + "="*60)
    if result:
        print("✅ 강의계획서 HTML 분석 완료!")
    else:
        print("❌ 강의계획서 HTML 분석 실패")