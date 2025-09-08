#!/usr/bin/env python3

"""
크롤링 상태 확인 및 완료 후 데이터 조회
"""

import asyncio
import logging
import json
import time
from app.services.auth_service import AuthService
from app.services.eclass_service import EclassService

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def wait_for_crawling_and_check_data():
    """크롤링 완료 대기 후 데이터 확인"""
    test_username = "22102482"
    test_password = "kim021206!"
    course_id = "A2025310911441009"
    
    try:
        # 1. 로그인
        auth_service = AuthService()
        login_result = await auth_service.eclass_login(test_username, test_password)
        user_id = login_result["user"]["id"]
        
        logger.info(f"✅ 로그인 성공: 사용자 ID {user_id}")
        
        # 2. EclassService 초기화
        eclass_service = EclassService()
        await eclass_service.login(test_username, test_password)
        
        # 3. 크롤링 작업 시작
        logger.info("🔄 새로운 크롤링 작업 시작")
        crawl_result = await eclass_service.crawl_course(user_id, course_id, auto_download=False, is_jwt_user=True)
        task_id = crawl_result.get("task_id")
        
        logger.info(f"📋 크롤링 작업 ID: {task_id}")
        
        # 4. 크롤링 상태 모니터링 (최대 30초 대기)
        max_wait_time = 30
        check_interval = 2
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            status_result = await eclass_service.get_task_status(task_id)
            status = status_result.get("status")
            
            logger.info(f"📊 크롤링 상태: {status} (경과 시간: {elapsed_time}초)")
            
            if status == "completed":
                logger.info("✅ 크롤링 완료!")
                result_data = status_result.get("result", {})
                details = result_data.get("details", {})
                logger.info(f"크롤링 결과 상세:")
                logger.info(f"  - 공지사항: {details.get('notices', {})}")
                logger.info(f"  - 강의자료: {details.get('materials', {})}")
                break
            elif status == "failed" or status == "error":
                logger.error(f"❌ 크롤링 실패: {status_result}")
                break
            
            await asyncio.sleep(check_interval)
            elapsed_time += check_interval
        
        # 5. 크롤링 완료 후 데이터 조회
        logger.info("📢 공지사항 조회")
        notices = await eclass_service.get_notices(user_id, course_id, is_jwt_user=True)
        
        logger.info("📚 강의자료 조회")
        materials = await eclass_service.get_materials(user_id, course_id, is_jwt_user=True)
        
        # 6. 결과 출력
        logger.info(f"=== 최종 결과 ===")
        logger.info(f"공지사항: {len(notices)}개")
        for i, notice in enumerate(notices[:2]):
            logger.info(f"  공지 {i+1}: {notice.get('title', 'N/A')}")
            logger.info(f"    내용: {notice.get('content', 'N/A')[:100]}...")
            logger.info(f"    첨부파일: {len(notice.get('attachments', []))}개")
            
        logger.info(f"강의자료: {len(materials)}개")
        for i, material in enumerate(materials[:2]):
            logger.info(f"  자료 {i+1}: {material.get('title', 'N/A')}")
            logger.info(f"    내용: {material.get('content', 'N/A')[:100]}...")
            logger.info(f"    첨부파일: {len(material.get('attachments', []))}개")
        
        # 7. 데이터가 있으면 샘플을 JSON으로 출력
        if notices or materials:
            logger.info("=== 샘플 데이터 구조 ===")
            if notices:
                logger.info("공지사항 샘플:")
                logger.info(json.dumps(notices[0], indent=2, ensure_ascii=False, default=str))
            if materials:
                logger.info("강의자료 샘플:")
                logger.info(json.dumps(materials[0], indent=2, ensure_ascii=False, default=str))
        else:
            logger.warning("⚠️ 크롤링 후에도 데이터가 없습니다. 해당 강의에 공지사항/강의자료가 없거나 크롤링이 제대로 되지 않은 것 같습니다.")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 테스트 중 오류 발생: {str(e)}")
        import traceback
        logger.error(f"상세 오류:\n{traceback.format_exc()}")
        return False

if __name__ == "__main__":
    result = asyncio.run(wait_for_crawling_and_check_data())
    if result:
        print("\n✅ 테스트 성공")
    else:
        print("\n❌ 테스트 실패")