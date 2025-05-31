#!/usr/bin/env python3
"""
Admin API를 사용하여 사용자를 활성화하는 스크립트
"""
import os
import sys
sys.path.append('/Users/elaus/PycharmProjects/AutoLMS-R')

from supabase import create_client
from app.core.config import settings

def activate_user_admin():
    try:
        # Service Role Key로 Admin 클라이언트 생성
        admin_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        print("✅ Admin 클라이언트 생성 성공")
        
        # 테스트 사용자 정보
        test_email = "testuser@seoultech.ac.kr"
        user_id = "c32d9a77-936e-4116-bce5-432cbe709ba3"
        
        # Admin API로 사용자 업데이트
        try:
            update_result = admin_client.auth.admin.update_user_by_id(
                user_id,
                {"email_confirm": True}
            )
            print(f"✅ Admin API로 사용자 활성화 완료: {update_result}")
            return True
            
        except Exception as admin_error:
            print(f"Admin API 실패: {admin_error}")
            
            # 대안: 사용자 확인 상태를 수동으로 설정
            try:
                # 이메일 확인된 상태로 업데이트
                confirm_result = admin_client.auth.admin.update_user_by_id(
                    user_id,
                    {
                        "user_metadata": {"email_verified": True},
                        "app_metadata": {"email_verified": True}
                    }
                )
                print(f"✅ 메타데이터 업데이트 완료: {confirm_result}")
                return True
                
            except Exception as meta_error:
                print(f"메타데이터 업데이트 실패: {meta_error}")
                
                # 최후 수단: 사용자 재생성 (이메일 확인 없이)
                try:
                    # 기존 사용자 삭제
                    delete_result = admin_client.auth.admin.delete_user(user_id)
                    print(f"기존 사용자 삭제: {delete_result}")
                    
                    # 새 사용자 생성 (이메일 확인 없이)
                    create_result = admin_client.auth.admin.create_user({
                        "email": test_email,
                        "password": "testpassword123",
                        "email_confirm": True  # 이메일 확인을 건너뜀
                    })
                    print(f"✅ 새 사용자 생성 (이메일 확인 없이): {create_result}")
                    return True
                    
                except Exception as recreate_error:
                    print(f"사용자 재생성 실패: {recreate_error}")
                    return False
        
    except Exception as e:
        print(f"❌ 전체 프로세스 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = activate_user_admin()
    if success:
        print("🎯 사용자 활성화 완료! 이제 로그인을 시도해보세요.")
    else:
        print("❌ 사용자 활성화 실패")
