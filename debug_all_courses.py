import asyncio
import logging
import os
import sys
sys.path.append('/Users/elaus/PycharmProjects/AutoLMS-R')

from app.services.eclass_session import EclassSession
from app.services.eclass_parser import EclassParser
from app.core.config import settings

# 로깅 설정
logging.basicConfig(level=logging.INFO)  # DEBUG -> INFO로 변경 (너무 많은 로그)
logger = logging.getLogger(__name__)

async def debug_all_courses():
    """모든 강의의 첨부파일 확인"""
    session = EclassSession()
    parser = EclassParser()
    
    try:
        # 로그인
        print("🔐 eClass 로그인 중...")
        login_success = await session.login(settings.ECLASS_USERNAME, settings.ECLASS_PASSWORD)
        if not login_success:
            print("❌ 로그인 실패")
            return
        print("✅ 로그인 성공")
        
        # 강의 목록 가져오기
        print("📚 강의 목록 조회 중...")
        course_html = await session.get_course_list()
        courses = parser.parse_courses(course_html)
        print(f"✅ 강의 {len(courses)}개 발견")
        
        for i, course in enumerate(courses):
            course_id = course['id']
            print(f"\n{'='*60}")
            print(f"🎯 강의 {i+1}/{len(courses)}: {course['name']} ({course_id})")
            print(f"{'='*60}")
            
            # 강의실 접근
            course_url = await session.access_course(course_id)
            if not course_url:
                print("❌ 강의실 접근 실패")
                continue
                
            # 강의 메뉴 파싱
            response = await session.get(course_url)
            course_menus = parser.parse_course_menus(response.text)
            print(f"📋 메뉴: {list(course_menus.keys())}")
            
            # 강의자료 메뉴가 있는지 확인
            if "lecture_material" not in course_menus:
                print("❌ 강의자료 메뉴 없음")
                continue
                
            # 강의자료 목록 가져오기
            material_url = course_menus["lecture_material"]["url"]
            base_url = "https://eclass.seoultech.ac.kr"
            material_url = f"{base_url}{material_url}" if not material_url.startswith("http") else material_url
            material_url = material_url.replace('lecture_material_list_form', 'lecture_material_list')
            
            response = await session.get(material_url)
            if not response:
                print("❌ 강의자료 목록 응답 없음")
                continue
                
            materials = parser.parse_material_list(response.text)
            print(f"📄 강의자료: {len(materials)}개")
            
            if not materials:
                print("⚠️ 강의자료 없음")
                continue
            
            # 첨부파일이 있는 자료 찾기
            materials_with_attachments = [m for m in materials if m.get('has_attachment', False)]
            print(f"📎 첨부파일 있는 자료: {len(materials_with_attachments)}개")
            
            # 첫 번째 첨부파일 있는 자료 상세 조회
            if materials_with_attachments:
                material = materials_with_attachments[0]
                print(f"\n🔍 첨부파일 있는 자료 상세 조회: '{material['title']}'")
                detail_response = await session.get(material["url"])
                
                if detail_response:
                    material_detail = await parser.parse_material_detail(session, detail_response.text, course_id)
                    attachments = material_detail.get('attachments', [])
                    print(f"📎 파싱된 첨부파일: {len(attachments)}개")
                    
                    for j, attachment in enumerate(attachments):
                        print(f"  📄 첨부파일 {j+1}: {attachment.get('name', 'No name')}")
                        print(f"      URL: {attachment.get('url', 'No URL')[:80]}...")
                    
                    if attachments:
                        print("✅ 첨부파일 발견! 이 강의로 테스트 가능")
                        break
                else:
                    print("❌ 상세 정보 응답 없음")
            else:
                # 첨부파일이 없는 경우도 몇 개 확인
                print("📋 첫 3개 자료 확인:")
                for j, material in enumerate(materials[:3]):
                    print(f"  {j+1}. {material.get('title', 'No title')}")
                    print(f"      첨부파일: {material.get('has_attachment', False)}")
        
        # 로그아웃
        await session.close()
        print("\n🚪 세션 종료")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_all_courses())
