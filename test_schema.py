#!/usr/bin/env python3
"""Supabase 테이블 스키마 확인"""

from supabase import create_client
from app.core.config import settings

def test_schema():
    """Supabase 테이블 스키마 확인"""
    # Service Key를 사용하여 RLS 우회
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    
    # UUID 형식으로 테스트
    test_uuid = 'af56401f-da61-44fb-a201-3bfe163ecee3'  # 실제 사용자 UUID
    
    test_cases = [
        # 1. user_id만 (UUID 형식)
        {'user_id': test_uuid},
        
        # 2. course_id 추가
        {'user_id': test_uuid, 'course_id': 'test_course'},
        
        # 3. course_name 추가
        {'user_id': test_uuid, 'course_id': 'test_course', 'course_name': 'Test Course'},
        
        # 4. created_at, updated_at 추가
        {
            'user_id': test_uuid, 
            'course_id': 'test_course', 
            'course_name': 'Test Course',
            'created_at': '2023-01-01T00:00:00',
            'updated_at': '2023-01-01T00:00:00'
        },
        
        # 5. 추가 필드들 테스트
        {
            'user_id': test_uuid, 
            'course_id': 'test_course2', 
            'course_name': 'Test Course 2',
            'instructor': '홍길동교수님',
            'semester': '2025-1학기',
            'year': '2025',
            'last_crawled': '2023-01-01T00:00:00',
            'created_at': '2023-01-01T00:00:00',
            'updated_at': '2023-01-01T00:00:00'
        }
    ]
    
    for i, test_data in enumerate(test_cases, 1):
        try:
            result = supabase.table('courses').insert(test_data).execute()
            print(f"Test {i} 성공: {test_data.keys()}")
            
            # 성공한 경우 생성된 레코드 삭제
            if result.data:
                record_id = result.data[0]['id']
                supabase.table('courses').delete().eq('id', record_id).execute()
                print(f"  -> 생성된 레코드 ID {record_id} 삭제됨")
                
        except Exception as e:
            print(f"Test {i} 실패: {e}")
            print(f"  -> 시도한 필드: {list(test_data.keys())}")

if __name__ == "__main__":
    test_schema()