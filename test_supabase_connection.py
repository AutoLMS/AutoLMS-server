#!/usr/bin/env python3
"""
Supabase 연결 테스트
"""
import asyncio
import logging
from app.core.supabase_client import get_supabase_client
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_supabase_connection():
    """Supabase 연결 테스트"""
    try:
        logger.info("Supabase 클라이언트 연결 테스트 시작")
        logger.info(f"Supabase URL: {settings.SUPABASE_URL}")
        
        # Supabase 클라이언트 생성
        supabase = get_supabase_client()
        
        # 간단한 테이블 조회 테스트
        logger.info("courses 테이블 조회 테스트...")
        result = supabase.table('courses').select('*').limit(5).execute()
        
        logger.info(f"✅ Supabase 연결 성공!")
        logger.info(f"조회된 courses 수: {len(result.data)}")
        
        if result.data:
            logger.info("첫 번째 course 샘플:")
            logger.info(f"  - ID: {result.data[0]['id']}")
            logger.info(f"  - Name: {result.data[0]['name']}")
            logger.info(f"  - User ID: {result.data[0]['user_id']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Supabase 연결 실패: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_supabase_connection())
