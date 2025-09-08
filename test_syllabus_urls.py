#!/usr/bin/env python3

"""
다양한 강의계획서 URL 테스트
"""

import asyncio
from app.services.auth_service import AuthService
from app.services.eclass_service import EclassService

async def test_syllabus_urls():
    """다양한 강의계획서 URL 형식 테스트"""
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
        base_url = "https://eclass.seoultech.ac.kr"
        
        # 다양한 URL 패턴 시도
        url_patterns = [
            f"{base_url}/lecture/course_info.jsp?ref=1&ud={user_id}&ky={course_id}",
            f"{base_url}/lecture/course_info.jsp?ky={course_id}",
            f"{base_url}/ilos/st/course/plan_form.acl?KJKEY={course_id}",
            f"{base_url}/ilos/st/course/submain_form.acl?KJKEY={course_id}&menu=plan",
            f"{base_url}/ilos/st/course/course_intro_form.acl?KJKEY={course_id}",
        ]
        
        print(f"🔍 강의계획서 URL 테스트 시작 (강의: {course_id})")
        print("=" * 80)
        
        for i, url in enumerate(url_patterns, 1):
            print(f"\n{i}. URL 테스트: {url}")
            print("-" * 60)
            
            try:
                response = await eclass_service.session.get(url)
                
                if response:
                    html_content = response.text
                    print(f"✅ 응답 성공 (길이: {len(html_content)} 문자)")
                    
                    # 방화벽 차단 확인
                    if "Web firewall security policies" in html_content:
                        print("❌ 웹 방화벽에 의해 차단됨")
                        continue
                    
                    # 로그인 리다이렉션 확인
                    if "login" in html_content.lower() or "로그인" in html_content:
                        print("🔑 로그인 페이지로 리다이렉션")
                        continue
                    
                    # 강의계획서 키워드 확인
                    keywords = ['수업기본정보', '담당교수정보', '강의계획', '주별강의계획', '강의명', '교수명', '강의개요']
                    found_keywords = []
                    
                    for keyword in keywords:
                        if keyword in html_content:
                            found_keywords.append(keyword)
                    
                    if found_keywords:
                        print(f"🎯 강의계획서 키워드 발견: {found_keywords}")
                        print(f"📄 HTML 샘플 (처음 500자):")
                        print(html_content[:500])
                        print("\n✅ 이 URL이 유효한 것 같습니다!")
                        
                        # 파싱 테스트
                        parsed_result = eclass_service.parser.parse_syllabus(html_content)
                        print(f"🧪 파싱 테스트 결과:")
                        for key, value in parsed_result.items():
                            if isinstance(value, (dict, list)) and value:
                                print(f"   ✅ {key}: 데이터 있음")
                            else:
                                print(f"   ❌ {key}: 데이터 없음")
                        
                        return url  # 성공한 URL 반환
                    else:
                        print(f"❓ 강의계획서 키워드 없음")
                        print(f"📄 HTML 샘플: {html_content[:200]}...")
                
                else:
                    print("❌ 응답 실패")
                    
            except Exception as e:
                print(f"❌ 오류: {str(e)}")
        
        print(f"\n" + "=" * 80)
        print("❌ 모든 URL 패턴에서 유효한 강의계획서를 찾을 수 없습니다.")
        return None
        
    except Exception as e:
        print(f"❌ 전체 테스트 실패: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None

if __name__ == "__main__":
    result = asyncio.run(test_syllabus_urls())
    print("\n" + "="*80)
    if result:
        print(f"✅ 유효한 강의계획서 URL 발견: {result}")
    else:
        print("❌ 유효한 강의계획서 URL을 찾을 수 없습니다.")