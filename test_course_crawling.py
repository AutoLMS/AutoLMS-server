#!/usr/bin/env python3
"""강의 내용 크롤링 테스트"""

import asyncio
import logging
from app.services.eclass_service import EclassService
from app.core.config import settings

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_course_crawling():
    """강의 크롤링 테스트"""
    service = EclassService()
    
    try:
        # 로그인
        print("로그인 시도...")
        login_success = await service.login(settings.ECLASS_USERNAME, settings.ECLASS_PASSWORD)
        if not login_success:
            print("로그인 실패")
            return
        print("로그인 성공")
        
        # 강의 목록 가져오기
        print("강의 목록 조회...")
        user_id = 'af56401f-da61-44fb-a201-3bfe163ecee3'  # 테스트 사용자 ID
        courses = await service.get_courses(user_id, force_refresh=True)
        print(f"강의 목록: {len(courses)}개")
        
        if courses:
            # 첫 번째 강의로 테스트
            first_course = courses[0]
            course_id = first_course.get('course_id') or first_course.get('id')
            course_name = first_course.get('course_name') or first_course.get('name', 'Unknown')
            print(f"테스트 강의: {course_name} (ID: {course_id})")
            
            # 강의 크롤링 시작
            print("강의 크롤링 시작...")
            result = await service.crawl_course(user_id, course_id, auto_download=False)
            print(f"크롤링 결과: {result}")
            
            # 작업 상태 확인
            if result.get('task_id'):
                await asyncio.sleep(3)  # 잠시 대기
                status = await service.get_task_status(result['task_id'])
                print(f"작업 상태: {status}")
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await service.close()

if __name__ == "__main__":
    asyncio.run(test_course_crawling())