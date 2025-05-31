#!/usr/bin/env python3
"""
데이터베이스 연결을 테스트하는 스크립트
"""
import asyncio
import sys
import os
sys.path.append('/Users/elaus/PycharmProjects/AutoLMS-R')

from urllib.parse import quote_plus, unquote
from app.core.config import settings

def check_database_url():
    """데이터베이스 URL 분석"""
    print(f"원본 DATABASE_URL: {settings.DATABASE_URL}")
    
    # URL 파싱
    if "%" in settings.DATABASE_URL:
        try:
            decoded_url = unquote(settings.DATABASE_URL)
            print(f"디코딩된 URL: {decoded_url}")
        except Exception as e:
            print(f"URL 디코딩 실패: {e}")
    
    # 패스워드 인코딩 테스트
    password = "rnrnrn3824+"
    encoded_password = quote_plus(password)
    print(f"원본 패스워드: {password}")
    print(f"인코딩된 패스워드: {encoded_password}")
    
    # 올바른 URL 구성
    correct_url = f"postgresql+asyncpg://postgres:{encoded_password}@db.evknhkmfwgbzmbdgfvme.supabase.co:5432/postgres"
    print(f"올바른 URL: {correct_url}")
    
    return correct_url

async def test_db_connection():
    """데이터베이스 연결 테스트"""
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        
        # 올바른 URL로 테스트
        correct_url = check_database_url()
        
        print("\n🔄 데이터베이스 연결 테스트 중...")
        engine = create_async_engine(correct_url, echo=False)
        
        async with engine.begin() as conn:
            result = await conn.execute("SELECT 1")
            print("✅ 데이터베이스 연결 성공!")
            
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_db_connection())
    if success:
        print("🎯 데이터베이스 연결 OK!")
    else:
        print("❌ 데이터베이스 연결 문제")
