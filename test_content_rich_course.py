#!/usr/bin/env python3
"""내용이 있는 강의 크롤링 테스트"""

import asyncio
import logging
from app.services.eclass_service import EclassService
from app.core.config import settings

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_content_rich_course():
    """내용이 있는 강의 크롤링 테스트"""
    service = EclassService()
    
    try:
        # 로그인
        print("로그인 시도...")
        login_success = await service.login(settings.ECLASS_USERNAME, settings.ECLASS_PASSWORD)
        if not login_success:
            print("로그인 실패")
            return
        print("로그인 성공")
        
        # 내용이 있는 강의 선택 (IT Project Management)
        user_id = 'af56401f-da61-44fb-a201-3bfe163ecee3'
        course_id = 'A2025114608541001'  # IT Project Management
        
        print(f"내용이 있는 강의 크롤링 시작: {course_id}")
        
        # 강의 크롤링 시작
        result = await service.crawl_course(user_id, course_id, auto_download=False)
        print(f"크롤링 시작 결과: {result}")
        
        # 작업 완료까지 대기
        task_id = result.get('task_id')
        if task_id:
            # 작업 완료 대기
            for i in range(10):  # 최대 10초 대기
                await asyncio.sleep(1)
                status = await service.get_task_status(task_id)
                print(f"작업 상태 {i+1}: {status.get('status')}")
                
                if status.get('status') in ['completed', 'failed']:
                    print(f"최종 결과: {status}")
                    if 'result' in status:
                        details = status['result'].get('details', {})
                        print("\n=== 크롤링 상세 결과 ===")
                        print(f"공지사항: {details.get('notices', {})}")
                        print(f"강의자료: {details.get('materials', {})}")
                        print(f"과제: {details.get('assignments', {})}")
                    break
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await service.close()

if __name__ == "__main__":
    asyncio.run(test_content_rich_course())