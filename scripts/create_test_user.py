import os
import sys
sys.path.append('/Users/elaus/PycharmProjects/AutoLMS-R')

from supabase import create_client, Client
import asyncio

# Supabase 설정
SUPABASE_URL = "https://evknhkmfwgbzmbdgfvme.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV2a25oa21md2diem1iZGdmdm1lIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MzIzNjI1MCwiZXhwIjoyMDU4ODEyMjUwfQ.tPcQ70w8Hn6p_NaflBTH1hBZhcUKC5BUh8xRtYM5fN8"  # Service role key

async def create_confirmed_user():
    try:
        # Service role로 클라이언트 생성
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        # 사용자 생성 (이메일 확인 없이)
        auth_response = supabase.auth.admin.create_user({
            "email": "apitest@example.com",
            "password": "testpassword123",
            "email_confirm": True  # 이메일 자동 확인
        })
        
        print("✅ 사용자 생성 성공:")
        print(f"사용자 ID: {auth_response.user.id}")
        print(f"이메일: {auth_response.user.email}")
        print(f"이메일 확인 여부: {auth_response.user.email_confirmed_at is not None}")
        
        return auth_response.user.id
        
    except Exception as e:
        print(f"❌ 사용자 생성 실패: {e}")
        return None

if __name__ == "__main__":
    user_id = asyncio.run(create_confirmed_user())
    if user_id:
        print(f"\n🎯 생성된 사용자 ID: {user_id}")
        print("📧 테스트 계정: apitest@example.com")
        print("🔑 비밀번호: testpassword123")
