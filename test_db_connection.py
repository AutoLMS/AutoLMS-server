import asyncio
import asyncpg
import sys
import os

# .env 파일에서 환경 변수 로드
sys.path.append('/Users/elaus/PycharmProjects/AutoLMS-R')
from dotenv import load_dotenv
load_dotenv()

async def test_db_connection():
    try:
        # 직접 연결 테스트
        conn = await asyncpg.connect(
            host="db.evknhkmfwgbzmbdgfvme.supabase.co",
            port=5432,
            database="postgres",
            user="postgres",
            password="rnrnrn3824+"
        )
        
        print("✅ 데이터베이스 연결 성공!")
        
        # 간단한 쿼리 테스트
        version = await conn.fetchval("SELECT version()")
        print(f"PostgreSQL 버전: {version}")
        
        # 테이블 존재 확인
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        print(f"공개 테이블 수: {len(tables)}")
        for table in tables[:5]:  # 처음 5개만 출력
            print(f"  - {table['table_name']}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_db_connection())
    if success:
        print("🎯 데이터베이스 연결 정상!")
    else:
        print("❌ 데이터베이스 연결 문제 있음")
