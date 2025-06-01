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

def test_table_columns(table_name, test_data):
    """테이블에 테스트 데이터 삽입을 시도해서 필요한 컬럼 파악"""
    try:
        print(f"\n=== {table_name} 테이블 컬럼 테스트 ===")
        result = supabase.table(table_name).insert(test_data).execute()
        print(f"✅ 성공: {result.data}")
        # 삽입된 데이터 삭제
        if result.data and len(result.data) > 0:
            delete_result = supabase.table(table_name).delete().eq('id', result.data[0]['id']).execute()
            print(f"🗑️ 테스트 데이터 삭제됨")
    except Exception as e:
        print(f"❌ 실패: {e}")
        if "Could not find" in str(e):
            missing_column = str(e).split("'")[1] if "'" in str(e) else "unknown"
            print(f"  누락된 컬럼: {missing_column}")

if __name__ == "__main__":
    # materials 테이블 테스트 (has_attachments 컬럼 확인)
    materials_test = {
        'user_id': 'test-user',
        'course_id': 'test-course',
        'article_id': 'test-article',
        'title': 'test title',
        'has_attachments': True  # 이 컬럼이 있는지 확인
    }
    test_table_columns('materials', materials_test)
    
    # attachments 테이블 테스트 (source_id 컬럼 확인)
    attachments_test = {
        'file_name': 'test.pdf',
        'source_id': 'test-source',  # 이 컬럼이 있는지 확인
        'source_type': 'materials',
        'course_id': 'test-course',
        'storage_path': '/test/path'
    }
    test_table_columns('attachments', attachments_test)
    
    # assignments 테이블 테스트
    assignments_test = {
        'user_id': 'test-user',
        'course_id': 'test-course',
        'assignment_id': 'test-assignment',
        'title': 'test assignment',
        'author': 'test author'  # 이 컬럼이 있는지 확인
    }
    test_table_columns('assignments', assignments_test)
