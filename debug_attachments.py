import asyncio
import logging
import os
import sys
sys.path.append('/Users/elaus/PycharmProjects/AutoLMS-R')

from app.services.eclass_session import EclassSession
from app.services.eclass_parser import EclassParser
from app.core.config import settings

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def debug_attachment_parsing():
    """첨부파일 파싱 디버깅"""
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
        
        # 첫 번째 강의 선택
        if not courses:
            print("❌ 강의가 없습니다")
            return
            
        course = courses[0]
        course_id = course['id']
        print(f"🎯 선택된 강의: {course['name']} ({course_id})")
        
        # 강의실 접근
        print("🚪 강의실 접근 중...")
        course_url = await session.access_course(course_id)
        if not course_url:
            print("❌ 강의실 접근 실패")
            return
        print(f"✅ 강의실 URL: {course_url}")
        
        # 강의 메뉴 파싱
        print("📋 강의 메뉴 파싱 중...")
        response = await session.get(course_url)
        course_menus = parser.parse_course_menus(response.text)
        print(f"✅ 파싱된 메뉴: {list(course_menus.keys())}")
        
        # 강의자료 메뉴가 있는지 확인
        if "lecture_material" not in course_menus:
            print("❌ 강의자료 메뉴가 없습니다")
            return
            
        # 강의자료 목록 가져오기
        print("📄 강의자료 목록 조회 중...")
        material_url = course_menus["lecture_material"]["url"]
        base_url = "https://eclass.seoultech.ac.kr"
        material_url = f"{base_url}{material_url}" if not material_url.startswith("http") else material_url
        material_url = material_url.replace('lecture_material_list_form', 'lecture_material_list')
        
        print(f"📡 강의자료 URL: {material_url}")
        response = await session.get(material_url)
        
        if not response:
            print("❌ 강의자료 목록 응답 없음")
            return
            
        materials = parser.parse_material_list(response.text)
        print(f"✅ 강의자료 {len(materials)}개 발견")
        
        # 각 강의자료 확인
        attachment_found = False
        for i, material in enumerate(materials):
            print(f"\n--- 강의자료 {i+1}: {material.get('title', 'Unknown')} ---")
            print(f"📎 첨부파일 있음: {material.get('has_attachment', False)}")
            print(f"🔗 URL: {material.get('url', 'No URL')}")
            print(f"📋 article_id: {material.get('article_id', 'No ID')}")
            
            # 첨부파일이 있는 첫 번째 자료 상세 조회
            if material.get('has_attachment', False) and not attachment_found:
                print(f"\n🔍 '{material['title']}' 상세 정보 조회 중...")
                detail_response = await session.get(material["url"])
                
                if detail_response:
                    # 상세 정보 파싱
                    material_detail = await parser.parse_material_detail(session, detail_response.text, course_id)
                    print(f"📝 상세 내용 길이: {len(material_detail.get('content', ''))}")
                    
                    attachments = material_detail.get('attachments', [])
                    print(f"📎 파싱된 첨부파일: {len(attachments)}개")
                    
                    for j, attachment in enumerate(attachments):
                        print(f"  첨부파일 {j+1}:")
                        print(f"    이름: {attachment.get('name', 'No name')}")
                        print(f"    URL: {attachment.get('url', 'No URL')}")
                        print(f"    파일 시퀀스: {attachment.get('file_seq', 'No seq')}")
                    
                    attachment_found = True
                    
                    # 전체 material 데이터 업데이트
                    material.update(material_detail)
                    print(f"📦 최종 material 데이터 키: {list(material.keys())}")
                    
                else:
                    print("❌ 상세 정보 응답 없음")
                    
        if not attachment_found:
            print("\n⚠️ 첨부파일이 있는 강의자료를 찾을 수 없습니다")
        
        # 로그아웃
        await session.close()
        print("\n🚪 세션 종료")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_attachment_parsing())
