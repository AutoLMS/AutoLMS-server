#!/usr/bin/env python3
"""Supabase 테이블 스키마 확인"""

from supabase import create_client
from app.core.config import settings

def check_table_schema():
    """테이블 스키마 확인"""
    # Service Key 사용
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    
    tables = ['notices', 'materials', 'assignments', 'attachments']
    
    for table in tables:
        print(f"\n=== {table} 테이블 ===")
        try:
            # 테이블의 첫 번째 레코드를 조회해서 스키마 확인
            result = supabase.table(table).select("*").limit(1).execute()
            
            if result.data:
                print("기존 데이터 예시:")
                print(result.data[0].keys())
            else:
                print("데이터가 없음 - 빈 레코드로 스키마 확인 시도")
                
                # 각 테이블에 맞는 테스트 데이터 삽입 시도
                test_data = {}
                
                if table == 'notices':
                    test_data = {
                        'article_id': 'test_123',
                        'course_id': 'test_course',
                        'title': 'Test Notice',
                        'content': 'Test Content',
                        'author': 'Test Author',
                        'date': '2023-01-01',
                        'views': 1
                    }
                elif table == 'materials':
                    test_data = {
                        'article_id': 'test_123',
                        'course_id': 'test_course', 
                        'title': 'Test Material',
                        'content': 'Test Content',
                        'author': 'Test Author',
                        'date': '2023-01-01',
                        'views': 1
                    }
                elif table == 'assignments':
                    test_data = {
                        'assignment_id': 'test_123',
                        'course_id': 'test_course',
                        'title': 'Test Assignment',
                        'content': 'Test Content',
                        'author': 'Test Author',
                        'date': '2023-01-01',
                        'views': 1
                    }
                elif table == 'attachments':
                    test_data = {
                        'file_name': 'test.pdf',
                        'original_url': 'http://test.com/test.pdf',
                        'storage_path': '/test/path',
                        'source_id': '1',
                        'source_type': 'notices',
                        'course_id': 'test_course',
                        'user_id': 'test_user'
                    }
                
                try:
                    insert_result = supabase.table(table).insert(test_data).execute()
                    if insert_result.data:
                        print(f"테스트 삽입 성공: {list(insert_result.data[0].keys())}")
                        # 삽입한 테스트 데이터 삭제
                        record_id = insert_result.data[0]['id']
                        supabase.table(table).delete().eq('id', record_id).execute()
                        print("테스트 데이터 삭제 완료")
                    else:
                        print("테스트 삽입 실패")
                except Exception as e:
                    print(f"테스트 삽입 오류: {e}")
                    
        except Exception as e:
            print(f"테이블 조회 오류: {e}")

if __name__ == "__main__":
    check_table_schema()