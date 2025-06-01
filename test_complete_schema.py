#!/usr/bin/env python3
"""완전한 스키마로 테스트"""

from supabase import create_client
from app.core.config import settings

def test_complete_schema():
    """user_id 포함해서 완전한 스키마 테스트"""
    # Service Key 사용
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    
    # 실제 course_id 가져오기
    courses_result = supabase.table('courses').select("id, user_id").limit(1).execute()
    if courses_result.data:
        actual_course_id = courses_result.data[0]['id']
        actual_user_id = courses_result.data[0]['user_id']
        print(f"실제 course ID: {actual_course_id}, user ID: {actual_user_id}")
        
        # 각 테이블에 완전한 데이터로 테스트
        test_cases = [
            {
                'table': 'notices',
                'data': {
                    'user_id': actual_user_id,
                    'course_id': actual_course_id,
                    'title': 'Test Notice'
                }
            },
            {
                'table': 'materials', 
                'data': {
                    'user_id': actual_user_id,
                    'course_id': actual_course_id,
                    'title': 'Test Material'
                }
            },
            {
                'table': 'assignments',
                'data': {
                    'user_id': actual_user_id,
                    'course_id': actual_course_id, 
                    'title': 'Test Assignment'
                }
            },
            {
                'table': 'attachments',
                'data': {
                    'user_id': actual_user_id,
                    'course_id': actual_course_id,
                    'file_name': 'test.pdf'
                }
            }
        ]
        
        for test_case in test_cases:
            table = test_case['table']
            data = test_case['data']
            
            print(f"\n=== {table} 테이블 테스트 ===")
            try:
                # 삽입 시도
                result = supabase.table(table).insert(data).execute()
                
                if result.data:
                    print(f"✅ 삽입 성공")
                    print(f"실제 스키마: {list(result.data[0].keys())}")
                    
                    # 삽입한 데이터 삭제
                    record_id = result.data[0]['id']
                    supabase.table(table).delete().eq('id', record_id).execute()
                    print("테스트 데이터 삭제 완료")
                else:
                    print("❌ 삽입 실패 - 응답 데이터 없음")
                    
            except Exception as e:
                print(f"❌ 삽입 오류: {e}")
    else:
        print("courses 테이블에서 데이터를 찾을 수 없음")

if __name__ == "__main__":
    test_complete_schema()