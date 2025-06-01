#!/usr/bin/env python3
"""
수정된 Attachment 스키마 테스트
"""
import asyncio
import uuid
from app.utils.attachment_helper import (
    create_attachment_data,
    create_attachment_data_from_download_result,
    create_attachment_data_from_parsed_attachment
)
from app.db.repositories.supabase_attachment_repository import SupabaseAttachmentRepository
from app.core.config import settings


async def test_attachment_helper():
    """헬퍼 함수 테스트"""
    print("=== Attachment Helper 함수 테스트 ===")
    
    # 테스트 데이터
    user_id = str(uuid.uuid4())
    course_id = "A2025114608241001"  # 실제 존재하는 course_id
    source_type = "notices"
    source_id = 123
    file_name = "test_document.pdf"
    
    # 1. 기본 헬퍼 함수 테스트
    print("\n1️⃣ 기본 헬퍼 함수 테스트...")
    attachment_data = create_attachment_data(
        user_id=user_id,
        course_id=course_id,
        source_type=source_type,
        source_id=source_id,
        file_name=file_name,
        original_url="https://example.com/test.pdf",
        storage_path="/test/path/test.pdf"
    )
    print(f"✅ 생성된 데이터: {attachment_data}")
    
    # 2. 다운로드 결과에서 생성 테스트
    print("\n2️⃣ 다운로드 결과에서 생성 테스트...")
    download_result = {
        "file_name": "downloaded_file.pdf",
        "original_url": "https://eclass.seoultech.ac.kr/test.pdf",
        "storage_path": "/storage/downloaded_file.pdf",
        "success": True,
        "file_size": 1024000,
        "content_type": "application/pdf"
    }
    
    attachment_data_2 = create_attachment_data_from_download_result(
        user_id=user_id,
        course_id=course_id,
        source_type="lecture_materials",
        source_id=456,
        download_result=download_result
    )
    print(f"✅ 다운로드 결과에서 생성: {attachment_data_2}")
    
    # 3. 파싱된 첨부파일에서 생성 테스트
    print("\n3️⃣ 파싱된 첨부파일에서 생성 테스트...")
    parsed_attachment = {
        "name": "parsed_attachment.docx",
        "url": "https://eclass.seoultech.ac.kr/download?file=123",
        "file_seq": "456"
    }
    
    attachment_data_3 = create_attachment_data_from_parsed_attachment(
        user_id=user_id,
        course_id=course_id,
        source_type="assignments",
        source_id=789,
        parsed_attachment=parsed_attachment
    )
    print(f"✅ 파싱된 첨부파일에서 생성: {attachment_data_3}")


async def test_supabase_insertion():
    """실제 Supabase 삽입 테스트"""
    print("\n=== Supabase 삽입 테스트 ===")
    
    try:
        # Repository 초기화
        attachment_repo = SupabaseAttachmentRepository()
        
        # 실제 course_id 가져오기 또는 생성
        from app.core.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        courses_result = supabase.table('courses').select("course_id").limit(1).execute()
        
        real_course_id = None
        test_course_created = False
        
        if courses_result.data:
            real_course_id = courses_result.data[0]['course_id']
            print(f"📋 기존 course_id 사용: {real_course_id}")
        else:
            # 테스트용 course 생성
            test_user_id = str(uuid.uuid4())
            test_course_data = {
                'course_id': 'TEST_COURSE_001',
                'user_id': test_user_id,
                'course_name': 'Test Course for Attachment',
                'instructor': 'Test Instructor',
            }
            
            course_result = supabase.table('courses').insert(test_course_data).execute()
            if course_result.data:
                real_course_id = course_result.data[0]['course_id']
                test_course_created = True
                print(f"📋 테스트용 course 생성: {real_course_id}")
            else:
                print("❌ 테스트용 course 생성 실패")
                return
        
        # 헬퍼 함수로 데이터 생성
        user_id = str(uuid.uuid4())
        attachment_data = create_attachment_data(
            user_id=user_id,
            course_id=real_course_id,
            source_type="notices",
            source_id=1,
            file_name="test_helper_file.pdf",
            original_url="https://example.com/test.pdf",
            storage_path="/test/path"
        )
        
        print(f"📝 삽입할 데이터: {attachment_data}")
        
        # Supabase에 삽입
        result = await attachment_repo.create(**attachment_data)
        
        if result:
            print(f"✅ Supabase 삽입 성공! ID: {result['id']}")
            print(f"📊 삽입된 데이터: {result}")
            
            # 테스트 데이터 삭제
            delete_success = await attachment_repo.delete(result['id'])
            if delete_success:
                print("🗑️ 테스트 데이터 삭제 완료")
            else:
                print("⚠️ 테스트 데이터 삭제 실패")
        else:
            print("❌ Supabase 삽입 실패")
        
        # 테스트용 course 삭제
        if test_course_created:
            try:
                supabase.table('courses').delete().eq('course_id', real_course_id).execute()
                print("🗑️ 테스트용 course 삭제 완료")
            except Exception as e:
                print(f"⚠️ 테스트용 course 삭제 실패: {e}")
            
    except Exception as e:
        print(f"❌ 테스트 중 오류: {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """메인 테스트 함수"""
    print("🚀 Attachment 스키마 수정사항 테스트 시작")
    
    # 헬퍼 함수 테스트
    await test_attachment_helper()
    
    # Supabase 삽입 테스트
    await test_supabase_insertion()
    
    print("\n🎉 테스트 완료!")


if __name__ == "__main__":
    asyncio.run(main())
