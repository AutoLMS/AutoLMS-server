import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# Supabase 클라이언트 생성
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

def check_table_schema(table_name):
    """테이블 스키마 확인"""
    try:
        # PostgreSQL의 information_schema를 사용해서 컬럼 정보 조회
        result = supabase.rpc('get_table_columns', {
            'table_name_param': table_name
        }).execute()
        
        if result.data:
            print(f"\n=== {table_name} 테이블 스키마 ===")
            for column in result.data:
                print(f"  {column['column_name']}: {column['data_type']} {'NOT NULL' if column['is_nullable'] == 'NO' else 'NULL'}")
        else:
            # RPC가 없으면 직접 SQL 실행
            print(f"\n=== {table_name} 테이블 샘플 데이터로 스키마 추측 ===")
            result = supabase.table(table_name).select('*').limit(1).execute()
            if result.data:
                print(f"  컬럼들: {list(result.data[0].keys())}")
            else:
                print(f"  데이터 없음")
                
    except Exception as e:
        print(f"{table_name} 테이블 스키마 조회 실패: {e}")

if __name__ == "__main__":
    tables = ['materials', 'attachments', 'assignments']
    
    for table in tables:
        check_table_schema(table)
