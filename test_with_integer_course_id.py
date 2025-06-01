#!/usr/bin/env python3
"""정수 course_id로 테스트"""

from supabase import create_client
from app.core.config import settings

def test_with_integer():
    """정수 course_id로 테스트"""
    # Service Key 사용
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    
    # courses 테이블의 실제 ID 사용
    print("courses 테이블에서 실제 ID 확인...")
    courses_result = supabase.table('courses').select("id").limit(1).execute()
    if courses_result.data:
        actual_course_id = courses_result.data[0]['id']
        print(f"실제 course ID: {actual_course_id} (타입: {type(actual_course_id)})")
        
        # 각 테이블에 실제 course_id 사용해서 테스트
        test_cases = [
            {
                'table': 'notices',
                'data': {
                    'course_id': actual_course_id,
                    'title': 'Test Notice'
                }
            },
            {
                'table': 'materials', 
                'data': {
                    'course_id': actual_course_id,
                    'title': 'Test Material'
                }
            },
            {
                'table': 'assignments',
                'data': {
                    'course_id': actual_course_id, 
                    'title': 'Test Assignment'
                }
            },
            {
                'table': 'attachments',
                'data': {
                    'course_id': actual_course_id
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
    test_with_integer()