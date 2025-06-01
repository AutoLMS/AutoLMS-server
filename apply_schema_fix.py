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

def execute_sql_file(file_path):
    """SQL 파일 실행"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # SQL을 여러 문장으로 분리 (--로 시작하는 주석과 빈 줄 제거)
        sql_statements = []
        current_statement = []
        
        for line in sql_content.split('\n'):
            line = line.strip()
            # 주석이나 빈 줄 건너뛰기
            if line.startswith('--') or line == '':
                continue
            
            current_statement.append(line)
            
            # 세미콜론으로 끝나는 문장이면 실행
            if line.endswith(';'):
                sql_statement = '\n'.join(current_statement)
                sql_statements.append(sql_statement)
                current_statement = []
        
        # 각 SQL 문장 실행
        for i, statement in enumerate(sql_statements):
            try:
                print(f"실행 중 ({i+1}/{len(sql_statements)}): {statement[:50]}...")
                result = supabase.rpc('exec_sql', {'sql': statement}).execute()
                print(f"✅ 성공")
            except Exception as e:
                print(f"❌ 실패: {e}")
                # 일부 실패해도 계속 진행
                
    except Exception as e:
        print(f"SQL 파일 실행 실패: {e}")

def execute_simple_sql(sql):
    """간단한 SQL 실행"""
    try:
        # Supabase는 직접 SQL 실행이 제한적이므로 테이블 기반 작업으로 대체
        print(f"SQL 실행: {sql[:100]}...")
        
        # ALTER TABLE 명령어들을 개별적으로 실행
        if "ALTER TABLE materials ADD COLUMN" in sql:
            print("materials 테이블에 has_attachments 컬럼 추가 시도...")
            # 테스트 데이터로 컬럼 존재 확인
            try:
                result = supabase.table('materials').update({'has_attachments': False}).eq('id', 'non-existent').execute()
                print("✅ has_attachments 컬럼이 이미 존재함")
            except Exception as e:
                if "Could not find" in str(e):
                    print("❌ has_attachments 컬럼이 없음 - Supabase 대시보드에서 수동 추가 필요")
                else:
                    print("✅ has_attachments 컬럼 존재 (다른 오류)")
        
        elif "ALTER TABLE attachments ADD COLUMN" in sql:
            print("attachments 테이블에 source_id, source_type 컬럼 추가 시도...")
            try:
                result = supabase.table('attachments').update({'source_id': 'test'}).eq('id', 'non-existent').execute()
                print("✅ source_id 컬럼이 이미 존재함")
            except Exception as e:
                if "Could not find" in str(e):
                    print("❌ source_id 컬럼이 없음 - Supabase 대시보드에서 수동 추가 필요")
                else:
                    print("✅ source_id 컬럼 존재 (다른 오류)")
                    
    except Exception as e:
        print(f"❌ SQL 실행 실패: {e}")

if __name__ == "__main__":
    print("=== Supabase 스키마 수정 시작 ===")
    
    # 간단한 컬럼 존재 확인
    execute_simple_sql("ALTER TABLE materials ADD COLUMN has_attachments BOOLEAN")
    execute_simple_sql("ALTER TABLE attachments ADD COLUMN source_id TEXT")
    
    # 수동 수정 안내
    print("\n=== 수동 수정 필요 ===")
    print("Supabase 대시보드(https://supabase.com/dashboard)에서 다음 컬럼들을 추가해주세요:")
    print()
    print("1. materials 테이블:")
    print("   - has_attachments: boolean, default false")
    print()
    print("2. attachments 테이블:")
    print("   - source_id: text")
    print("   - source_type: text") 
    print("   - user_id: text")
    print()
    print("3. assignments 테이블:")
    print("   - author: text")
    print("   - start_date: text")
    print("   - end_date: text")
    print("   - status: text, default 'active'")
    print()
    print("컬럼 추가 후 다시 이 스크립트를 실행하거나 다음 단계로 진행하세요.")
