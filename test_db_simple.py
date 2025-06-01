#!/usr/bin/env python3
"""간단한 데이터베이스 연결 테스트"""

import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

async def test_db_connection():
    """데이터베이스 연결 테스트"""
    # 환경변수에서 DATABASE_URL 가져오기
    database_url = "postgresql+asyncpg://postgres:rnrnrn3824%2B@uukkvisuqhopdraeaawz.supabase.co:5432/postgres"
    
    try:
        print(f"데이터베이스 연결 시도: {database_url}")
        
        # 엔진 생성
        engine = create_async_engine(
            database_url,
            pool_pre_ping=True,
            echo=True,
            pool_size=1,
            max_overflow=0,
            pool_timeout=10
        )
        
        # 세션 생성
        async_session = async_sessionmaker(bind=engine, expire_on_commit=False)
        
        async with async_session() as session:
            print("세션 생성 성공")
            
            # 간단한 쿼리 실행
            result = await session.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            print(f"쿼리 실행 성공: {row}")
            
            # 테이블 존재 확인
            result = await session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            tables = result.fetchall()
            print(f"테이블 목록: {[t[0] for t in tables]}")
            
        await engine.dispose()
        print("연결 테스트 완료")
        
    except Exception as e:
        print(f"연결 실패: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_db_connection())