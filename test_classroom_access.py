#!/usr/bin/env python3

"""
강의실 접근 후 강의계획서 테스트
"""

import asyncio
from app.services.auth_service import AuthService
from app.services.eclass_service import EclassService

async def test_classroom_access():
    """강의실 접근 후 강의계획서 가져오기"""
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
        
        course_id = "A2025310911441009"
        
        print(f"🏫 강의실 접근 테스트 (강의: {course_id})")
        print("=" * 60)
        
        # 1. 강의실 접근
        print("1. 강의실 접근 시도...")
        classroom_url = await eclass_service.session.access_course(course_id)
        
        if not classroom_url:
            print("❌ 강의실 접근 실패")
            return False
        
        print(f"✅ 강의실 URL: {classroom_url}")
        
        # 2. 강의실 메인 페이지 접근
        print("\n2. 강의실 메인 페이지 접근...")
        response = await eclass_service.session.get(classroom_url)
        
        if not response:
            print("❌ 강의실 메인 페이지 접근 실패")
            return False
        
        print(f"✅ 메인 페이지 응답 (길이: {len(response.text)} 문자)")
        
        # 3. 메뉴 파싱으로 강의계획서 메뉴 확인
        print("\n3. 메뉴 파싱...")
        menus = eclass_service.parser.parse_course_menus(response.text)
        
        print(f"발견된 메뉴: {list(menus.keys())}")
        
        if 'plan' in menus:
            plan_url = menus['plan']['url']
            print(f"✅ 강의계획서 메뉴 발견: {plan_url}")
            
            # 4. 강의계획서 페이지 접근
            print("\n4. 강의계획서 페이지 직접 접근...")
            base_url = "https://eclass.seoultech.ac.kr"
            full_plan_url = f"{base_url}{plan_url}" if not plan_url.startswith("http") else plan_url
            
            plan_response = await eclass_service.session.get(full_plan_url)
            
            if plan_response:
                html_content = plan_response.text
                print(f"✅ 강의계획서 페이지 응답 (길이: {len(html_content)} 문자)")
                
                # 키워드 확인
                keywords = ['수업기본정보', '담당교수정보', '강의계획', '주별강의계획', '강의명', '교수명']
                found_keywords = []
                
                for keyword in keywords:
                    if keyword in html_content:
                        found_keywords.append(keyword)
                
                if found_keywords:
                    print(f"🎯 강의계획서 키워드 발견: {found_keywords}")
                    
                    # 파싱 테스트
                    print("\n5. 강의계획서 파싱 테스트...")
                    parsed_result = eclass_service.parser.parse_syllabus(html_content)
                    
                    has_data = False
                    for key, value in parsed_result.items():
                        if isinstance(value, dict) and value:
                            print(f"   ✅ {key}: {len(value)}개 항목")
                            has_data = True
                        elif isinstance(value, list) and value:
                            print(f"   ✅ {key}: {len(value)}개 항목")  
                            has_data = True
                        else:
                            print(f"   ❌ {key}: 데이터 없음")
                    
                    if has_data:
                        print("🎉 강의계획서 파싱 성공!")
                        return True
                    else:
                        print("❓ 파싱은 되지만 데이터가 비어있음")
                        print(f"📄 HTML 샘플: {html_content[:1000]}...")
                else:
                    print(f"❓ 강의계획서 키워드 없음")
                    print(f"📄 HTML 샘플: {html_content[:500]}...")
            else:
                print("❌ 강의계획서 페이지 응답 실패")
        else:
            print("❌ 강의계획서 메뉴를 찾을 수 없음")
            print(f"사용 가능한 메뉴: {list(menus.keys())}")
        
        return False
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    result = asyncio.run(test_classroom_access())
    print("\n" + "="*60)
    if result:
        print("✅ 강의실 접근을 통한 강의계획서 가져오기 성공!")
    else:
        print("❌ 강의실 접근을 통한 강의계획서 가져오기 실패")