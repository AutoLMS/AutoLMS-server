#!/usr/bin/env python3
"""
실제 eClass 크롤링을 테스트하는 스크립트 (DB 없이)
"""
import asyncio
import sys
import json
import os
from datetime import datetime
sys.path.append('/Users/elaus/PycharmProjects/AutoLMS-R')

from app.services.eclass_service import EclassService
from app.core.config import settings

async def test_eclass_crawling():
    """실제 eClass 크롤링 테스트"""
    print("🔄 실제 eClass 크롤링 테스트 시작...")
    
    try:
        # EClass 서비스 초기화
        eclass_service = EclassService()
        
        # 1. 로그인 테스트
        print(f"📧 eClass 로그인 시도: {settings.ECLASS_USERNAME}")
        login_success = await eclass_service.login(settings.ECLASS_USERNAME, settings.ECLASS_PASSWORD)
        
        if not login_success:
            print("❌ eClass 로그인 실패")
            return False
        
        print("✅ eClass 로그인 성공!")
        
        # 2. 강의 목록 크롤링 테스트
        print("📚 강의 목록 크롤링 중...")
        courses = await eclass_service.get_courses_without_db()  # DB 없이 크롤링
        
        print(f"✅ 강의 {len(courses)}개 발견:")
        for i, course in enumerate(courses[:3]):  # 처음 3개만 출력
            print(f"  {i+1}. {course.get('name', 'Unknown')} ({course.get('id', 'No ID')})")
        
        # 3. 첫 번째 강의의 상세 정보 크롤링
        if courses:
            first_course = courses[0]
            course_id = first_course.get('id')
            course_name = first_course.get('name')
            
            print(f"\n📖 '{course_name}' 강의 상세 크롤링 중...")
            
            # 공지사항 크롤링
            notices = await eclass_service.get_notices_without_db(course_id)
            print(f"📢 공지사항: {len(notices)}개")
            
            # 강의자료 크롤링
            materials = await eclass_service.get_materials_without_db(course_id)
            print(f"📄 강의자료: {len(materials)}개")
            
            # 과제 크롤링
            assignments = await eclass_service.get_assignments_without_db(course_id)
            print(f"📝 과제: {len(assignments)}개")
            
            # 첨부파일 확인
            attachment_count = 0
            for material in materials:
                if material.get('has_attachment', False):
                    attachment_count += 1
            
            print(f"📎 첨부파일이 있는 자료: {attachment_count}개")
            
            # 크롤링 결과를 JSON 파일로 저장
            crawl_result = {
                "timestamp": datetime.now().isoformat(),
                "courses_count": len(courses),
                "test_course": {
                    "id": course_id,
                    "name": course_name,
                    "notices_count": len(notices),
                    "materials_count": len(materials),
                    "assignments_count": len(assignments),
                    "attachments_count": attachment_count
                },
                "sample_notices": notices[:2] if notices else [],
                "sample_materials": materials[:2] if materials else [],
                "sample_assignments": assignments[:2] if assignments else []
            }
            
            # 결과 저장
            output_file = "test_data/crawl_test_result.json"
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(crawl_result, f, ensure_ascii=False, indent=2)
            
            print(f"💾 크롤링 결과 저장: {output_file}")
        
        # 4. 로그아웃
        await eclass_service.logout()
        print("🚪 eClass 로그아웃 완료")
        
        return True
        
    except Exception as e:
        print(f"❌ 크롤링 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_eclass_crawling())
    if success:
        print("🎯 실제 eClass 크롤링 테스트 성공!")
    else:
        print("❌ 실제 eClass 크롤링 테스트 실패")
