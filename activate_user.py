import os
import sys
sys.path.append('/Users/elaus/PycharmProjects/AutoLMS-R')

from app.core.supabase_client import get_supabase_client
import asyncio

async def manual_activate_user():
    try:
        client = get_supabase_client()
        
        # SQL 함수를 생성하여 사용자 활성화
        create_function_sql = """
        CREATE OR REPLACE FUNCTION public.activate_test_user(user_email text)
        RETURNS void AS $$
        BEGIN
          UPDATE auth.users 
          SET email_confirmed_at = NOW(),
              confirmed_at = NOW()
          WHERE email = user_email;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
        """
        
        # 함수 생성
        client.rpc('sql', {'query': create_function_sql}).execute()
        print("✅ SQL 함수 생성 완료")
        
        # 사용자 활성화
        result = client.rpc('activate_test_user', {'user_email': 'testuser123@gmail.com'}).execute()
        print("✅ 사용자 활성화 완료")
        
        return True
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        
        # 다른 방법 시도
        try:
            # 직접 SQL 실행 시도
            result = client.rpc('exec_sql', {
                'sql': "UPDATE auth.users SET email_confirmed_at = NOW(), confirmed_at = NOW() WHERE email = 'testuser123@gmail.com'"
            }).execute()
            print("✅ 직접 SQL 실행 완료")
            return True
        except Exception as e2:
            print(f"❌ 두 번째 시도도 실패: {e2}")
            return False

if __name__ == "__main__":
    success = asyncio.run(manual_activate_user())
    if success:
        print("🎯 이제 로그인을 시도해보세요!")
    else:
        print("❌ 수동 활성화 실패. 다른 방법 필요.")
