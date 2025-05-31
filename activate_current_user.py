#!/usr/bin/env python3
"""
현재 테스트 사용자를 활성화하는 스크립트
"""
import os
import sys
sys.path.append('/Users/elaus/PycharmProjects/AutoLMS-R')

from app.core.supabase_client import get_supabase_client

def activate_user():
    try:
        client = get_supabase_client()
        print("✅ Supabase 클라이언트 연결 성공")
        
        # 테스트 사용자 이메일
        test_email = "testuser@seoultech.ac.kr"
        
        # 사용자 조회
        user_result = client.table('auth.users').select('*').eq('email', test_email).execute()
        print(f"📧 사용자 조회 결과: {user_result.data}")
        
        if not user_result.data:
            print(f"❌ 사용자를 찾을 수 없습니다: {test_email}")
            return False
            
        user_id = user_result.data[0]['id']
        print(f"🆔 사용자 ID: {user_id}")
        
        # SQL 함수 생성
        create_function_sql = """
        CREATE OR REPLACE FUNCTION public.activate_test_user(user_email text)
        RETURNS json AS $$
        DECLARE
            result_count integer;
        BEGIN
            UPDATE auth.users 
            SET email_confirmed_at = NOW(),
                confirmed_at = NOW()
            WHERE email = user_email;
            
            GET DIAGNOSTICS result_count = ROW_COUNT;
            
            RETURN json_build_object(
                'success', true,
                'updated_rows', result_count,
                'message', 'User activated successfully'
            );
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
        """
        
        # RPC 함수로 SQL 실행
        try:
            # 함수 생성 (auth 스키마에 접근할 수 있는 SECURITY DEFINER 함수)
            create_result = client.rpc('exec', {'sql': create_function_sql}).execute()
            print("✅ SQL 함수 생성 완료")
            
            # 사용자 활성화 함수 호출
            activate_result = client.rpc('activate_test_user', {'user_email': test_email}).execute()
            print(f"✅ 사용자 활성화 완료: {activate_result.data}")
            
        except Exception as rpc_error:
            print(f"RPC 실행 실패: {rpc_error}")
            
            # 대안 방법: Service Role Key 사용
            try:
                from supabase import create_client
                from app.core.config import settings
                
                # Service Role Key로 클라이언트 재생성
                admin_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
                
                # Admin API 사용하여 사용자 업데이트
                update_result = admin_client.auth.admin.update_user_by_id(
                    user_id,
                    {"email_confirm": True}
                )
                print(f"✅ Admin API로 사용자 활성화 완료: {update_result}")
                
            except Exception as admin_error:
                print(f"Admin API 실패: {admin_error}")
                return False
        
        # 확인
        updated_user = client.table('auth.users').select('email, email_confirmed_at, confirmed_at').eq('email', test_email).execute()
        print(f"🔍 업데이트 후 사용자 상태: {updated_user.data}")
        
        return True
        
    except Exception as e:
        print(f"❌ 전체 프로세스 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = activate_user()
    if success:
        print("🎯 사용자 활성화 완료! 이제 로그인을 시도해보세요.")
    else:
        print("❌ 사용자 활성화 실패")
