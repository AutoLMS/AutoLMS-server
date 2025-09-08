#!/usr/bin/env python3

"""
강의 ID A2025310911441009로 실제 크롤링 테스트
스웨거 UI 응답 vs 실제 응답 내용 비교
"""

import asyncio
import logging
import json
from app.services.auth_service import AuthService
from app.services.eclass_service import EclassService

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_crawling_with_course_id():
    """강의 크롤링 및 공지사항/강의자료 조회 테스트"""
    test_username = "22102482"
    test_password = "kim021206!"
    course_id = "A2025310911441009"
    
    logger.info(f"=== 강의 크롤링 테스트 시작 ===")
    logger.info(f"테스트 계정: {test_username}")
    logger.info(f"강의 ID: {course_id}")
    
    try:
        # 1. 로그인
        auth_service = AuthService()
        login_result = await auth_service.eclass_login(test_username, test_password)
        user_id = login_result["user"]["id"]
        
        logger.info(f"✅ 로그인 성공: 사용자 ID {user_id}")
        
        # 2. EclassService 초기화 및 로그인
        eclass_service = EclassService()
        eclass_login_success = await eclass_service.login(test_username, test_password)
        
        if not eclass_login_success:
            logger.error("❌ eClass 서비스 로그인 실패")
            return False
            
        logger.info("✅ eClass 서비스 로그인 성공")
        
        # 3. 강의 크롤링
        logger.info(f"🔄 강의 크롤링 시작: {course_id}")
        crawl_result = await eclass_service.crawl_course(user_id, course_id, auto_download=False, is_jwt_user=True)
        
        logger.info("📊 크롤링 결과:")
        logger.info(json.dumps(crawl_result, indent=2, ensure_ascii=False))
        
        # 4. 공지사항 조회
        logger.info(f"📢 공지사항 조회 시작")
        notices = await eclass_service.get_notices(user_id, course_id, is_jwt_user=True)
        
        logger.info(f"📊 공지사항 결과: {len(notices)}개")
        for i, notice in enumerate(notices[:3]):  # 처음 3개만 출력
            logger.info(f"  공지사항 {i+1}:")
            logger.info(f"    - ID: {notice.get('article_id', 'N/A')}")
            logger.info(f"    - 제목: {notice.get('title', 'N/A')}")
            logger.info(f"    - 작성자: {notice.get('author', 'N/A')}")
            logger.info(f"    - 내용 길이: {len(notice.get('content', '')) if notice.get('content') else 0}자")
            logger.info(f"    - 첨부파일: {len(notice.get('attachments', []))}개")
            if notice.get('content'):
                content_preview = notice.get('content', '')[:100] + "..." if len(notice.get('content', '')) > 100 else notice.get('content', '')
                logger.info(f"    - 내용 미리보기: {content_preview}")
        
        # 5. 강의자료 조회
        logger.info(f"📚 강의자료 조회 시작")
        materials = await eclass_service.get_materials(user_id, course_id, is_jwt_user=True)
        
        logger.info(f"📊 강의자료 결과: {len(materials)}개")
        for i, material in enumerate(materials[:3]):  # 처음 3개만 출력
            logger.info(f"  강의자료 {i+1}:")
            logger.info(f"    - ID: {material.get('article_id', 'N/A')}")
            logger.info(f"    - 제목: {material.get('title', 'N/A')}")
            logger.info(f"    - 작성자: {material.get('author', 'N/A')}")
            logger.info(f"    - 내용 길이: {len(material.get('content', '')) if material.get('content') else 0}자")
            logger.info(f"    - 첨부파일: {len(material.get('attachments', []))}개")
            if material.get('content'):
                content_preview = material.get('content', '')[:100] + "..." if len(material.get('content', '')) > 100 else material.get('content', '')
                logger.info(f"    - 내용 미리보기: {content_preview}")
        
        # 6. 응답 데이터 구조 분석
        logger.info("=== 응답 데이터 구조 분석 ===")
        if notices:
            sample_notice = notices[0]
            logger.info("공지사항 샘플 데이터 구조:")
            logger.info(f"키 목록: {list(sample_notice.keys())}")
            
        if materials:
            sample_material = materials[0]
            logger.info("강의자료 샘플 데이터 구조:")
            logger.info(f"키 목록: {list(sample_material.keys())}")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ 테스트 중 오류 발생: {str(e)}")
        import traceback
        logger.error(f"상세 오류:\n{traceback.format_exc()}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_crawling_with_course_id())
    if result:
        print("\n✅ 크롤링 테스트 성공")
    else:
        print("\n❌ 크롤링 테스트 실패")