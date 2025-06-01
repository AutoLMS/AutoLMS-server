#!/usr/bin/env python3
"""Supabase 테이블에 빈 레코드 삽입해서 스키마 확인"""

from supabase import create_client
from app.core.config import settings

def test_minimal_inserts():
    """최소한의 데이터로 테이블 스키마 확인"""
    # Service Key 사용
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    
    # 각 테이블에 최소한의 데이터만 삽입 시도
    test_cases = [
        {
            'table': 'notices',
            'data': {
                'course_id': 'test_course',
                'title': 'Test Notice'
            }
        },
        {
            'table': 'materials', 
            'data': {
                'course_id': 'test_course',
                'title': 'Test Material'
            }
        },
        {
            'table': 'assignments',
            'data': {
                'course_id': 'test_course', 
                'title': 'Test Assignment'
            }
        },
        {
            'table': 'attachments',
            'data': {
                'course_id': 'test_course'
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

if __name__ == "__main__":
    test_minimal_inserts()