#!/usr/bin/env python3
"""
간단한 Attachment 직접 삽입 테스트
"""
import uuid
from app.core.supabase_client import get_supabase_client
from app.utils.attachment_helper import create_attachment_data

def test_direct_attachment():
    """Service Key로 직접 attachment 삽입 테스트"""
    print("🧪 Service Key로 직접 attachment 삽입 테스트")
    
    try:
        supabase = get_supabase_client()
        
        # 헬퍼 함수로 데이터 생성
        user_id = str(uuid.uuid4())
        attachment_data = create_attachment_data(
            user_id=user_id,
            course_id="TEST_COURSE_FOR_ATTACHMENT",  # 임의의 course_id
            source_type="notices",
            source_id=1,
            file_name="direct_test_file.pdf",
            original_url="https://example.com/direct_test.pdf",
            storage_path="/direct/test/path"
        )
        
        print(f"📝 삽입할 데이터: {attachment_data}")
        
        # Service Key로 직접 삽입 (RLS 우회)
        result = supabase.table('attachments').insert(attachment_data).execute()
        
        if result.data:
            print(f"✅ 직접 삽입 성공! ID: {result.data[0]['id']}")
            print(f"📊 삽입된 데이터: {result.data[0]}")
            
            # 테스트 데이터 삭제
            record_id = result.data[0]['id']
            supabase.table('attachments').delete().eq('id', record_id).execute()
            print("🗑️ 테스트 데이터 삭제 완료")
        else:
            print("❌ 직접 삽입 실패")
            
    except Exception as e:
        print(f"❌ 테스트 중 오류: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_direct_attachment()
