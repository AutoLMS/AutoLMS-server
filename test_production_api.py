#!/usr/bin/env python3

"""
Production API 테스트 (ENVIRONMENT를 production으로 설정해서 테스트)
"""

import asyncio
import os
from unittest.mock import patch
from app.services.auth_service import AuthService
from app.core.config import settings

async def test_production_flow():
    """Production 환경에서의 API 플로우 테스트"""
    try:
        # 환경을 임시로 production으로 변경
        original_env = settings.ENVIRONMENT
        settings.ENVIRONMENT = "production"
        
        print(f"🔧 환경 변경: {original_env} → {settings.ENVIRONMENT}")
        
        # 로그인 테스트
        auth_service = AuthService()
        login_result = await auth_service.eclass_login("22102482", "kim021206!")
        user_id = login_result["user"]["id"]
        
        print(f"✅ 로그인 성공: {user_id}")
        
        # 자격증명 조회 테스트
        try:
            creds = await auth_service.get_user_eclass_credentials(user_id)
            print(f"✅ 자격증명 조회 성공:")
            print(f"   - Username: {creds['eclass_username']}")
            print(f"   - Password length: {len(creds['eclass_password'])}")
            
            # 실제 eClass 로그인 테스트
            from app.services.eclass_service import EclassService
            eclass_service = EclassService()
            
            login_success = await eclass_service.login(
                creds["eclass_username"], 
                creds["eclass_password"]
            )
            
            if login_success:
                print("✅ eClass 로그인 성공!")
                
                # 강의 목록 조회 테스트
                courses = await eclass_service.get_courses(user_id, force_refresh=True, is_jwt_user=True)
                print(f"✅ 강의 목록 조회 성공: {len(courses)}개")
                
                return True
            else:
                print("❌ eClass 로그인 실패")
                return False
                
        except Exception as e:
            print(f"❌ 자격증명 조회 실패: {str(e)}")
            return False
            
    except Exception as e:
        print(f"❌ 전체 테스트 실패: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False
    finally:
        # 환경 복원
        settings.ENVIRONMENT = original_env
        print(f"🔧 환경 복원: {settings.ENVIRONMENT}")

if __name__ == "__main__":
    result = asyncio.run(test_production_flow())
    print("\n" + "="*50)
    if result:
        print("✅ Production API 플로우 테스트 성공!")
        print("스웨거 UI에서 /api/v1/courses/ 엔드포인트가 정상 작동할 것입니다.")
    else:
        print("❌ Production API 플로우 테스트 실패")