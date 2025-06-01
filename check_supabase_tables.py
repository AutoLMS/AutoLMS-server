#!/usr/bin/env python3
"""Supabase 테이블 존재 여부 확인"""

from supabase import create_client
from app.core.config import settings

def check_tables_exist():
    """테이블 존재 여부 확인"""
    # Service Key 사용
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    
    tables = ['courses', 'notices', 'materials', 'assignments', 'attachments']
    
    for table in tables:
        print(f"\n=== {table} 테이블 확인 ===")
        try:
            # 테이블에서 0개 레코드 조회 (테이블 존재 여부만 확인)
            result = supabase.table(table).select("*").limit(0).execute()
            print(f"✅ {table} 테이블 존재함")
            
            # 실제 레코드 수 확인
            count_result = supabase.table(table).select("*", count="exact").execute()
            print(f"   레코드 수: {count_result.count}")
            
            # 첫 번째 레코드로 스키마 확인
            sample_result = supabase.table(table).select("*").limit(1).execute()
            if sample_result.data:
                print(f"   컬럼: {list(sample_result.data[0].keys())}")
            else:
                print("   데이터 없음")
                
        except Exception as e:
            print(f"❌ {table} 테이블 오류: {e}")

if __name__ == "__main__":
    check_tables_exist()