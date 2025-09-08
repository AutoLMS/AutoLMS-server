#!/usr/bin/env python3

"""
eClass 로그인 타임아웃 문제 테스트
학번 22102482 계정으로 sign_in_with_password 블로킹 이슈 검증
"""

import asyncio
import logging
import time
from app.services.auth_service import AuthService

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_eclass_login_timeout():
    """eClass 로그인 타임아웃 테스트"""
    test_username = "22102482"
    test_password = "kim021206!"  # 탈출문자 없는 실제 비밀번호
    
    logger.info(f"=== eClass 로그인 타임아웃 테스트 시작 ===")
    logger.info(f"테스트 계정: {test_username}")
    
    auth_service = AuthService()
    
    # 1. eClass 직접 로그인 테스트
    logger.info("1. eClass 직접 로그인 테스트")
    start_time = time.time()
    
    try:
        from app.services.eclass_service import EclassService
        eclass_service = EclassService()
        
        logger.info("eClass 서비스 로그인 시도...")
        eclass_result = await asyncio.wait_for(
            eclass_service.login(test_username, test_password),
            timeout=60.0  # 60초 타임아웃
        )
        
        elapsed = time.time() - start_time
        logger.info(f"eClass 직접 로그인 결과: {eclass_result}")
        logger.info(f"소요 시간: {elapsed:.2f}초")
        
    except asyncio.TimeoutError:
        elapsed = time.time() - start_time
        logger.error(f"eClass 로그인 타임아웃! 소요시간: {elapsed:.2f}초")
        return False
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"eClass 로그인 오류: {str(e)}, 소요시간: {elapsed:.2f}초")
        return False
    
    # 2. AuthService 통합 로그인 테스트
    logger.info("2. AuthService 통합 로그인 테스트")
    start_time = time.time()
    
    try:
        logger.info("AuthService 로그인 시도...")
        auth_result = await asyncio.wait_for(
            auth_service.eclass_login(test_username, test_password),
            timeout=120.0  # 120초 타임아웃
        )
        
        elapsed = time.time() - start_time
        logger.info(f"AuthService 로그인 성공!")
        logger.info(f"소요 시간: {elapsed:.2f}초")
        logger.info(f"결과: {auth_result}")
        
        return True
        
    except asyncio.TimeoutError:
        elapsed = time.time() - start_time
        logger.error(f"AuthService 로그인 타임아웃! 소요시간: {elapsed:.2f}초")
        return False
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"AuthService 로그인 오류: {str(e)}, 소요시간: {elapsed:.2f}초")
        import traceback
        logger.error(f"상세 오류:\n{traceback.format_exc()}")
        return False

async def test_supabase_auth_only():
    """Supabase Auth sign_in_with_password만 테스트"""
    logger.info("3. Supabase Auth sign_in_with_password 직접 테스트")
    
    from app.core.supabase_client import get_supabase_client
    
    # 22102482 계정의 가상 이메일과 고정 비밀번호
    virtual_email = "seoultech_22102482@autolms.internal"
    fixed_password = "autolms_22102482_2024"
    
    start_time = time.time()
    
    try:
        supabase = get_supabase_client()
        logger.info(f"Supabase 로그인 시도: {virtual_email}")
        
        auth_response = await asyncio.wait_for(
            asyncio.to_thread(
                supabase.auth.sign_in_with_password,
                {
                    "email": virtual_email,
                    "password": fixed_password
                }
            ),
            timeout=30.0  # 30초 타임아웃
        )
        
        elapsed = time.time() - start_time
        
        if auth_response.user and auth_response.session:
            logger.info(f"Supabase 로그인 성공! 소요시간: {elapsed:.2f}초")
            logger.info(f"사용자 ID: {auth_response.user.id}")
            return True
        else:
            logger.error(f"Supabase 로그인 실패: 사용자나 세션이 없음, 소요시간: {elapsed:.2f}초")
            return False
            
    except asyncio.TimeoutError:
        elapsed = time.time() - start_time
        logger.error(f"Supabase 로그인 타임아웃! 소요시간: {elapsed:.2f}초")
        return False
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"Supabase 로그인 오류: {str(e)}, 소요시간: {elapsed:.2f}초")
        import traceback
        logger.error(f"상세 오류:\n{traceback.format_exc()}")
        return False

async def main():
    """메인 테스트 함수"""
    logger.info("=== 로그인 타임아웃 문제 진단 시작 ===")
    
    # 각 단계별 테스트
    results = []
    
    # Step 1: eClass 직접 로그인 테스트
    results.append(await test_eclass_login_timeout())
    
    # Step 2: Supabase Auth만 테스트 (계정이 있다면)
    # results.append(await test_supabase_auth_only())
    
    # Step 3: 전체 통합 테스트 (필요시)
    # results.append(await test_eclass_login_timeout())
    
    logger.info("=== 테스트 결과 요약 ===")
    logger.info(f"성공한 테스트: {sum(results)}/{len(results)}")
    
    if not any(results):
        logger.error("모든 테스트 실패! 블로킹 이슈 확인됨")
    else:
        logger.info("일부 테스트 성공, 문제 구간 식별 가능")

if __name__ == "__main__":
    asyncio.run(main())