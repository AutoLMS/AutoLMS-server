#!/usr/bin/env python3

"""
모든 기능 통합 테스트 스크립트
공지사항, 강의자료, 강의계획서, 과제, 첨부파일 등 전체 기능 확인
"""

import asyncio
import logging
import json
from app.services.auth_service import AuthService
from app.services.eclass_service import EclassService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_all_features():
    """모든 기능 통합 테스트"""
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
        
        logger.info("=" * 60)
        logger.info("🔄 전체 기능 테스트 시작")
        logger.info("=" * 60)
        
        # 1. 크롤링 실행
        logger.info("🕷️ 크롤링 시작...")
        crawl_result = await eclass_service.crawl_course(user_id, course_id, auto_download=False, is_jwt_user=True)
        task_id = crawl_result.get("task_id")
        
        # 완료 대기
        for i in range(15):  # 최대 30초 대기
            await asyncio.sleep(2)
            status_result = await eclass_service.get_task_status(task_id)
            if status_result.get("status") == "completed":
                logger.info("✅ 크롤링 완료!")
                break
        
        logger.info("=" * 60)
        
        # 2. 공지사항 테스트
        logger.info("📢 공지사항 테스트")
        logger.info("-" * 40)
        try:
            notices = await eclass_service.get_notices(user_id, course_id, is_jwt_user=True)
            logger.info(f"공지사항 개수: {len(notices)}")
            if notices:
                notice = notices[0]
                logger.info(f"✅ 첫 번째 공지: {notice.get('title', 'N/A')[:50]}")
                logger.info(f"   작성자: {notice.get('author', 'N/A')}")
                logger.info(f"   첨부파일: {len(notice.get('attachments', []))}개")
            else:
                logger.warning("⚠️ 공지사항이 없습니다")
        except Exception as e:
            logger.error(f"❌ 공지사항 조회 실패: {str(e)}")
        
        # 3. 강의자료 테스트
        logger.info("📚 강의자료 테스트")
        logger.info("-" * 40)
        try:
            materials = await eclass_service.get_materials(user_id, course_id, is_jwt_user=True)
            logger.info(f"강의자료 개수: {len(materials)}")
            if materials:
                material = materials[0]
                logger.info(f"✅ 첫 번째 자료: {material.get('title', 'N/A')[:50]}")
                logger.info(f"   작성자: {material.get('author', 'N/A')}")
                logger.info(f"   첨부파일: {len(material.get('attachments', []))}개")
            else:
                logger.warning("⚠️ 강의자료가 없습니다")
        except Exception as e:
            logger.error(f"❌ 강의자료 조회 실패: {str(e)}")
        
        # 4. 강의계획서 테스트
        logger.info("📋 강의계획서 테스트")
        logger.info("-" * 40)
        try:
            syllabus = await eclass_service.get_syllabus(user_id, course_id)
            logger.info(f"강의계획서 조회 결과: {bool(syllabus)}")
            if syllabus:
                logger.info(f"✅ 강의계획서 키: {list(syllabus.keys())}")
                if '수업기본정보' in syllabus:
                    basic_info = syllabus['수업기본정보']
                    logger.info(f"   수업명: {basic_info.get('수업명', 'N/A')}")
                    logger.info(f"   담당교수: {basic_info.get('담당교수', 'N/A')}")
            else:
                logger.warning("⚠️ 강의계획서가 없습니다")
        except Exception as e:
            logger.error(f"❌ 강의계획서 조회 실패: {str(e)}")
        
        # 5. 과제 테스트
        logger.info("📝 과제 테스트")
        logger.info("-" * 40)
        try:
            assignments = await eclass_service.get_assignments(user_id, course_id, is_jwt_user=True)
            logger.info(f"과제 개수: {len(assignments)}")
            if assignments:
                assignment = assignments[0]
                logger.info(f"✅ 첫 번째 과제: {assignment.get('title', 'N/A')[:50]}")
                logger.info(f"   마감일: {assignment.get('due_date', 'N/A')}")
                logger.info(f"   첨부파일: {len(assignment.get('attachments', []))}개")
            else:
                logger.warning("⚠️ 과제가 없습니다")
        except Exception as e:
            logger.error(f"❌ 과제 조회 실패: {str(e)}")
        
        logger.info("=" * 60)
        
        # 6. 종합 결과
        results = {}
        
        # 각 기능별 데이터 존재 여부 확인
        try:
            notices = await eclass_service.get_notices(user_id, course_id, is_jwt_user=True)
            results['notices'] = len(notices)
        except:
            results['notices'] = 'ERROR'
            
        try:
            materials = await eclass_service.get_materials(user_id, course_id, is_jwt_user=True)
            results['materials'] = len(materials)
        except:
            results['materials'] = 'ERROR'
            
        try:
            syllabus = await eclass_service.get_syllabus(user_id, course_id)
            results['syllabus'] = 'OK' if syllabus else 'EMPTY'
        except:
            results['syllabus'] = 'ERROR'
            
        try:
            assignments = await eclass_service.get_assignments(user_id, course_id, is_jwt_user=True)
            results['assignments'] = len(assignments)
        except:
            results['assignments'] = 'ERROR'
        
        logger.info("🎯 종합 결과")
        logger.info("-" * 40)
        logger.info(f"📢 공지사항: {results['notices']}")
        logger.info(f"📚 강의자료: {results['materials']}")
        logger.info(f"📋 강의계획서: {results['syllabus']}")
        logger.info(f"📝 과제: {results['assignments']}")
        
        # 성공/실패 판단
        errors = sum(1 for v in results.values() if v == 'ERROR')
        if errors == 0:
            logger.info("🎉 모든 기능이 정상 작동합니다!")
            return True
        else:
            logger.warning(f"⚠️ {errors}개 기능에 오류가 있습니다.")
            return False
            
    except Exception as e:
        logger.error(f"❌ 테스트 실패: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    result = asyncio.run(test_all_features())
    print("\n" + "="*60)
    if result:
        print("✅ 전체 기능 테스트 성공!")
    else:
        print("❌ 일부 기능에 문제가 있습니다.")