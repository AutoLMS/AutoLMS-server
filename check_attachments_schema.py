#!/usr/bin/env python3
"""Attachments 테이블 스키마 정확히 확인"""

from supabase import create_client
from app.core.config import settings
import uuid

def check_attachments_schema():
    """Attachments 테이블의 실제 스키마 확인"""
    # Service Key 사용
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    
    print("=== Attachments 테이블 스키마 확인 ===")
    
    # 0. 실제 course_id 가져오기
    try:
        courses_result = supabase.table('courses').select("course_id").limit(1).execute()
        if courses_result.data:
            real_course_id = courses_result.data[0]['course_id']
            print(f"✅ 실제 course_id 사용: {real_course_id}")
        else:
            print("❌ courses 테이블에 데이터가 없습니다.")
            return
    except Exception as e:
        print(f"❌ courses 테이블 조회 오류: {e}")
        return
    
    # 1. 기존 데이터 확인
    try:
        result = supabase.table('attachments').select("*").limit(1).execute()
        if result.data:
            print("✅ 기존 데이터 예시:")
            print(f"컬럼: {list(result.data[0].keys())}")
            print(f"데이터: {result.data[0]}")
        else:
            print("📝 기존 데이터가 없어서 테스트 삽입으로 스키마 확인")
    except Exception as e:
        print(f"❌ 기존 데이터 조회 오류: {e}")
    
    # 2. 테스트 데이터로 스키마 확인 (실제 course_id 사용)
    test_data = {
        'file_name': 'test_file.pdf',
        'original_filename': 'original_test_file.pdf',  # NOT NULL 필드
        'stored_filename': 'stored_test_file.pdf',  # NOT NULL 필드
        'original_url': 'https://example.com/test.pdf',
        'storage_path': '/test/path',
        'source_id': '1',
        'source_type': 'notices',
        'course_id': real_course_id,  # 실제 course_id 사용
        'user_id': str(uuid.uuid4()),  # UUID 형태로 테스트
        'related_type': 'notices',  # NOT NULL 필드 추가
        'related_id': '1',  # NOT NULL 필드 추가
    }
    
    try:
        print("\n🧪 테스트 데이터 삽입 시도...")
        print(f"테스트 데이터: {test_data}")
        
        result = supabase.table('attachments').insert(test_data).execute()
        
        if result.data:
            print("✅ 테스트 삽입 성공!")
            print(f"실제 스키마: {list(result.data[0].keys())}")
            print(f"삽입된 데이터: {result.data[0]}")
            
            # 테스트 데이터 삭제
            record_id = result.data[0]['id']
            supabase.table('attachments').delete().eq('id', record_id).execute()
            print("🗑️ 테스트 데이터 삭제 완료")
        else:
            print("❌ 테스트 삽입 실패 - 응답 데이터 없음")
            
    except Exception as e:
        print(f"❌ 테스트 삽입 오류: {e}")
        
        # 오류 메시지 분석
        error_msg = str(e)
        if 'null value' in error_msg and 'violates not-null constraint' in error_msg:
            print("🔍 NOT NULL 제약조건 위반 - 필수 필드 누락")
        elif 'invalid input syntax for type uuid' in error_msg:
            print("🔍 UUID 타입 오류 - user_id가 UUID 타입인 것 같음")
        elif 'column' in error_msg and 'does not exist' in error_msg:
            print("🔍 컬럼이 존재하지 않음")

if __name__ == "__main__":
    check_attachments_schema()
