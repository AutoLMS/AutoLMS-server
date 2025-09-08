#!/usr/bin/env python3

"""
최종 크롤링 테스트 - 스키마 문제 해결 후
"""

import asyncio
import logging
import json
from app.services.auth_service import AuthService
from app.services.eclass_service import EclassService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def final_crawling_test():
    """최종 크롤링 및 데이터 확인 테스트"""
    test_username = "22102482"
    test_password = "kim021206!"
    course_id = "A2025310911441009"
    
    try:
        # 로그인
        auth_service = AuthService()
        login_result = await auth_service.eclass_login(test_username, test_password)
        user_id = login_result["user"]["id"]
        
        eclass_service = EclassService()
        await eclass_service.login(test_username, test_password)
        
        # 크롤링 실행
        logger.info("🔄 최종 크롤링 테스트 시작")
        crawl_result = await eclass_service.crawl_course(user_id, course_id, auto_download=False, is_jwt_user=True)
        task_id = crawl_result.get("task_id")
        
        # 완료 대기
        for i in range(15):  # 최대 30초 대기
            await asyncio.sleep(2)
            status_result = await eclass_service.get_task_status(task_id)
            if status_result.get("status") == "completed":
                logger.info("✅ 크롤링 완료!")
                break
        
        # 데이터 조회
        logger.info("📢 공지사항 조회")
        notices = await eclass_service.get_notices(user_id, course_id, is_jwt_user=True)
        
        logger.info("📚 강의자료 조회")
        materials = await eclass_service.get_materials(user_id, course_id, is_jwt_user=True)
        
        # 결과 출력
        logger.info(f"=== 최종 결과 ===")
        logger.info(f"공지사항: {len(notices)}개")
        logger.info(f"강의자료: {len(materials)}개")
        
        if notices:
            logger.info("✅ 공지사항 데이터 확인됨:")
            notice = notices[0]
            logger.info(f"  - 제목: {notice.get('title', 'N/A')}")
            logger.info(f"  - 작성자: {notice.get('author', 'N/A')}")
            logger.info(f"  - 내용: {notice.get('content', 'N/A')[:100]}...")
            logger.info(f"  - 첨부파일: {len(notice.get('attachments', []))}개")
            
            # API 응답 형태로 변환 테스트
            api_response = {
                "notices": notices,
                "total": len(notices)
            }
            logger.info("📝 API 응답 샘플:")
            logger.info(json.dumps(api_response, indent=2, ensure_ascii=False, default=str)[:500] + "...")
            
        if materials:
            logger.info("✅ 강의자료 데이터 확인됨:")
            material = materials[0]
            logger.info(f"  - 제목: {material.get('title', 'N/A')}")
            logger.info(f"  - 작성자: {material.get('author', 'N/A')}")
            logger.info(f"  - 내용: {material.get('content', 'N/A')[:100]}...")
            logger.info(f"  - 첨부파일: {len(material.get('attachments', []))}개")
        
        # 결론
        if notices or materials:
            logger.info("🎉 성공! 스웨거 UI에서 이제 데이터가 보일 것입니다.")
            return True
        else:
            logger.warning("⚠️ 여전히 데이터가 없습니다.")
            return False
            
    except Exception as e:
        logger.error(f"❌ 테스트 실패: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    result = asyncio.run(final_crawling_test())
    print("\n" + "="*50)
    if result:
        print("✅ 최종 테스트 성공! 스웨거 UI 문제 해결됨")
    else:
        print("❌ 최종 테스트 실패 - 추가 디버깅 필요")