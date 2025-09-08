#!/usr/bin/env python3

"""
인증 플로우 테스트 - 스웨거 UI와 동일한 흐름으로 테스트
"""

import asyncio
from app.services.auth_service import AuthService

async def test_auth_flow():
    """스웨거 UI와 동일한 인증 플로우 테스트"""
    try:
        # 1. 로그인 테스트
        print("1️⃣ eClass 로그인 테스트...")
        auth_service = AuthService()
        
        try:
            login_result = await auth_service.eclass_login("22102482", "kim021206!")
            user_id = login_result["user"]["id"]
            print(f"✅ 로그인 성공: {user_id}")
        except Exception as e:
            print(f"❌ 로그인 실패: {e}")
            return False
        
        # 2. 자격증명 조회 테스트
        print("\n2️⃣ 사용자 자격증명 조회 테스트...")
        
        try:
            creds = await auth_service.get_user_eclass_credentials(user_id)
            print(f"✅ 자격증명 조회 성공:")
            print(f"   - Username: {creds['eclass_username']}")
            print(f"   - Password length: {len(creds['eclass_password'])}")
            print(f"   - Password starts with: {creds['eclass_password'][:3]}...")
        except Exception as e:
            print(f"❌ 자격증명 조회 실패: {e}")
            import traceback
            print(f"트레이스백: {traceback.format_exc()}")
            return False
        
        # 3. eClass 서비스 로그인 테스트
        print("\n3️⃣ eClass 서비스 로그인 테스트...")
        
        try:
            from app.services.eclass_service import EclassService
            eclass_service = EclassService()
            
            login_success = await eclass_service.login(
                creds["eclass_username"], 
                creds["eclass_password"]
            )
            print(f"✅ eClass 서비스 로그인 결과: {login_success}")
            
            if not login_success:
                print("❌ eClass 서비스 로그인 실패")
                return False
                
        except Exception as e:
            print(f"❌ eClass 서비스 로그인 중 오류: {e}")
            import traceback
            print(f"트레이스백: {traceback.format_exc()}")
            return False
        
        # 4. 강의 목록 조회 테스트
        print("\n4️⃣ 강의 목록 조회 테스트...")
        
        try:
            courses = await eclass_service.get_courses(user_id, force_refresh=True, is_jwt_user=True)
            print(f"✅ 강의 목록 조회 성공: {len(courses)}개")
            
            if courses:
                print(f"   - 첫 번째 강의: {courses[0].get('name', 'N/A')}")
            
            return True
            
        except Exception as e:
            print(f"❌ 강의 목록 조회 실패: {e}")
            import traceback
            print(f"트레이스백: {traceback.format_exc()}")
            return False
            
    except Exception as e:
        print(f"❌ 전체 테스트 실패: {e}")
        import traceback
        print(f"트레이스백: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_auth_flow())
    print("\n" + "="*60)
    if result:
        print("✅ 전체 인증 플로우 테스트 성공!")
        print("API 엔드포인트가 정상 작동해야 합니다.")
    else:
        print("❌ 인증 플로우에 문제가 있습니다.")
        print("스웨거 UI에서도 동일한 오류가 발생할 것입니다.")