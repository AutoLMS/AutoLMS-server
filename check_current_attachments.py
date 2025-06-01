#!/usr/bin/env python3
"""현재 DB에 저장된 첨부파일 데이터 확인"""

from supabase import create_client
from app.core.config import settings
from collections import Counter

def check_current_attachments():
    """현재 Supabase에 저장된 첨부파일 데이터 확인"""
    # Service Key 사용
    supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    
    print("=== 현재 저장된 첨부파일 데이터 확인 ===")
    
    try:
        # 전체 첨부파일 수 확인
        count_result = supabase.table('attachments').select("*", count="exact").execute()
        total_count = count_result.count
        print(f"📊 총 첨부파일 수: {total_count}")
        
        if total_count == 0:
            print("📝 첨부파일 데이터가 없습니다.")
            return
        
        # 최근 5개 데이터 조회
        result = supabase.table('attachments').select("*").order('created_at', desc=True).limit(5).execute()
        
        if result.data:
            print(f"\n📋 최근 {len(result.data)}개 첨부파일:")
            for i, attachment in enumerate(result.data):
                print(f"\n--- 첨부파일 {i+1} ---")
                print(f"ID: {attachment.get('id')}")
                print(f"파일명: {attachment.get('file_name', 'N/A')}")
                print(f"원본 파일명: {attachment.get('original_filename', 'N/A')}")
                print(f"저장 파일명: {attachment.get('stored_filename', 'N/A')}")
                print(f"소스 타입: {attachment.get('source_type', 'N/A')}")
                print(f"소스 ID: {attachment.get('source_id', 'N/A')}")
                print(f"강의 ID: {attachment.get('course_id', 'N/A')}")
                print(f"사용자 ID: {attachment.get('user_id', 'N/A')}")
                print(f"원본 URL: {attachment.get('original_url', 'N/A')[:100]}...")
                print(f"저장 경로: {attachment.get('storage_path', 'N/A')}")
                print(f"생성일: {attachment.get('created_at', 'N/A')}")
        
        # source_type별 분포 확인
        print(f"\n📈 source_type별 분포:")
        source_types = supabase.table('attachments').select("source_type").execute()
        if source_types.data:
            type_counts = Counter(item['source_type'] for item in source_types.data)
            for source_type, count in type_counts.items():
                print(f"  {source_type}: {count}개")
        
        # 강의별 분포 확인
        print(f"\n📚 강의별 분포:")
        course_result = supabase.table('attachments').select("course_id").execute()
        if course_result.data:
            course_counts = Counter(item['course_id'] for item in course_result.data)
            for course_id, count in course_counts.items():
                print(f"  {course_id}: {count}개")
                
        # storage_path가 비어있는 데이터 확인
        empty_storage = supabase.table('attachments').select("*").or_("storage_path.is.null,storage_path.eq.").execute()
        print(f"\n💾 storage_path가 비어있는 첨부파일: {len(empty_storage.data)}개")
        
        if len(empty_storage.data) > 0:
            print("⚠️ 실제 파일이 업로드되지 않은 첨부파일들:")
            for attachment in empty_storage.data[:3]:  # 처음 3개만 표시
                print(f"  - {attachment.get('file_name', 'N/A')} (ID: {attachment.get('id')})")
                
    except Exception as e:
        print(f"❌ 첨부파일 데이터 조회 오류: {e}")

if __name__ == "__main__":
    check_current_attachments()
