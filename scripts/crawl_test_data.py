import asyncio
import sys
import json
import os
from datetime import datetime
sys.path.append('/Users/elaus/PycharmProjects/AutoLMS-R')

from app.services.eclass_session import EclassSession  
from app.services.eclass_parser import EclassParser
from app.core.config import settings

async def crawl_and_save_test_data():
    try:
        print("🔍 eClass 크롤링 및 테스트 데이터 생성 시작...")
        
        session = EclassSession()
        parser = EclassParser()
        
        print(f"📧 로그인 계정: {settings.ECLASS_USERNAME}")
        
        # eClass 로그인
        login_success = await session.login(
            settings.ECLASS_USERNAME, 
            settings.ECLASS_PASSWORD
        )
        
        if not login_success:
            print("❌ eClass 로그인 실패")
            return False
            
        print("✅ eClass 로그인 성공!")
        
        # 강의 목록 HTML 가져오기
        courses_html = await session.get_course_list()
        if not courses_html:
            print("❌ 강의 목록 HTML 가져오기 실패")
            return False
            
        # 강의 목록 파싱
        courses = parser.parse_courses(courses_html)
        print(f"📚 발견된 강의 수: {len(courses)}")
        
        # 테스트 데이터 구조 생성
        test_data = {
            "user_id": "1ae6fcaa-c18d-40a7-83bb-56715689b47c",
            "timestamp": datetime.now().isoformat(),
            "courses": courses,
            "course_details": {}
        }
        
        # 처음 2개 강의의 상세 정보 크롤링
        for i, course in enumerate(courses[:2]):
            course_id = course.get('id')
            course_name = course.get('name', 'Unknown')
            
            print(f"\n🔍 강의 '{course_name}' 상세 크롤링...")
            
            try:
                # 강의실 접근
                course_url = await session.access_course(course_id)
                if not course_url:
                    print(f"❌ 강의실 접근 실패: {course_id}")
                    continue
                    
                # 강의 메뉴 확인
                response = await session.get(course_url)
                course_menus = parser.parse_course_menus(response.text)
                
                course_detail = {
                    "id": course_id,
                    "name": course_name,
                    "menus": course_menus,
                    "notices": [],
                    "materials": [],
                    "assignments": []
                }
                
                # 공지사항 크롤링
                if "notice" in course_menus:
                    try:
                        base_url = "https://eclass.seoultech.ac.kr"
                        notice_url = f"{base_url}{course_menus['notice']['url']}"
                        notice_url = notice_url.replace('notice_list_form', 'notice_list')
                        
                        data = {
                            'start': '1',
                            'display': '10',
                            'SCH_VALUE': '',
                            'ud': session.user_id,
                            'ky': course_id,
                            'encoding': 'utf-8'
                        }
                        
                        response = await session.post(notice_url, data=data)
                        if response:
                            notices = parser.parse_notice_list(response.text)
                            course_detail["notices"] = notices
                            print(f"📢 공지사항 수: {len(notices)}")
                    except Exception as e:
                        print(f"❌ 공지사항 크롤링 오류: {e}")
                
                # 강의자료 크롤링
                if "lecture_material" in course_menus:
                    try:
                        material_url = f"{base_url}{course_menus['lecture_material']['url']}"
                        material_url = material_url.replace('lecture_material_list_form', 'lecture_material_list')
                        
                        response = await session.get(material_url)
                        if response:
                            materials = parser.parse_material_list(response.text)
                            course_detail["materials"] = materials
                            print(f"📄 강의자료 수: {len(materials)}")
                    except Exception as e:
                        print(f"❌ 강의자료 크롤링 오류: {e}")
                
                # 과제 크롤링
                if "assignment" in course_menus:
                    try:
                        assignment_url = f"{base_url}{course_menus['assignment']['url']}"
                        response = await session.get(assignment_url)
                        if response:
                            assignments = parser.parse_assignment_list(response.text)
                            course_detail["assignments"] = assignments
                            print(f"📝 과제 수: {len(assignments)}")
                    except Exception as e:
                        print(f"❌ 과제 크롤링 오류: {e}")
                
                test_data["course_details"][course_id] = course_detail
                
            except Exception as e:
                print(f"❌ 강의 {course_id} 크롤링 오류: {e}")
                continue
        
        # 테스트 데이터를 JSON 파일로 저장
        os.makedirs("test_data", exist_ok=True)
        
        with open("test_data/eclass_test_data.json", "w", encoding="utf-8") as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 테스트 데이터 저장 완료: test_data/eclass_test_data.json")
        print(f"📊 크롤링 결과:")
        print(f"  - 전체 강의 수: {len(courses)}")
        print(f"  - 상세 정보 수집 강의 수: {len(test_data['course_details'])}")
        
        for course_id, detail in test_data["course_details"].items():
            print(f"  - {detail['name']}: 공지 {len(detail['notices'])}개, 자료 {len(detail['materials'])}개, 과제 {len(detail['assignments'])}개")
        
        return test_data
        
    except Exception as e:
        print(f"❌ 크롤링 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(crawl_and_save_test_data())
    if result:
        print("\n🎉 eClass 크롤링 및 테스트 데이터 생성 성공!")
        print("✨ 이제 이 데이터를 API 응답에 사용할 수 있습니다!")
    else:
        print("\n❌ eClass 크롤링 실패")
