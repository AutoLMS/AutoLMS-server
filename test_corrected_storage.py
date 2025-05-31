#!/usr/bin/env python3
"""
수정된 Supabase Storage 테스트
"""
import asyncio
import logging
import tempfile
import os
from app.core.supabase_client import get_supabase_client
from app.services.file_handler import FileHandler
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_corrected_storage():
    """수정된 Storage 테스트"""
    try:
        logger.info("=== 수정된 Supabase Storage 테스트 ===")
        
        # 1. 설정 확인
        logger.info(f"1️⃣ 설정 확인...")
        logger.info(f"   SUPABASE_BUCKET: {settings.SUPABASE_BUCKET}")
        
        # 2. Supabase 클라이언트 및 bucket 확인
        supabase = get_supabase_client()
        buckets = supabase.storage.list_buckets()
        logger.info(f"   사용 가능한 buckets: {[b.name for b in buckets]}")
        
        # 3. 테스트 파일 생성
        logger.info("2️⃣ 테스트 파일 생성...")
        test_content = f"""# AutoLMS Storage 테스트 파일

Bucket: {settings.SUPABASE_BUCKET}
생성 시간: 2025-05-31 15:30:00
테스트 목적: 파일 업로드 및 다운로드 기능 검증

## 테스트 내용
1. ✅ 파일 생성
2. ⏳ FileHandler를 통한 업로드
3. ⏳ 직접 Storage API 테스트
4. ⏳ 메타데이터 저장

테스트 진행 중...
""".encode('utf-8')
        
        # 4. FileHandler 테스트
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.md', delete=False) as temp_file:
            temp_file.write(test_content)
            temp_path = temp_file.name
        
        try:
            logger.info("3️⃣ FileHandler 업로드 테스트...")
            file_handler = FileHandler()
            
            storage_url = await file_handler.upload_to_supabase(
                temp_path,
                'A2025114608241001',  # course_id
                'test',               # source_type  
                'corrected_test_001'  # article_id
            )
            
            if storage_url:
                logger.info(f"✅ FileHandler 업로드 성공!")
                logger.info(f"   Storage URL: {storage_url}")
                
                # 5. 직접 Storage API 테스트
                logger.info("4️⃣ 직접 Storage API 테스트...")
                
                # 파일 목록 확인
                files = supabase.storage.from_(settings.SUPABASE_BUCKET).list('courses/A2025114608241001/')
                logger.info(f"📁 저장된 파일 수: {len(files) if files else 0}개")
                
                if files:
                    for file in files:
                        logger.info(f"  📄 {file.get('name', 'Unknown')} ({file.get('updated_at', 'Unknown')})")
                
                # 6. 추가 테스트 파일 직접 업로드
                logger.info("5️⃣ 직접 API 업로드 테스트...")
                
                test_content_2 = b"Direct upload test via corrected bucket settings"
                direct_path = "courses/A2025114608241001/test/direct/corrected_direct.txt"
                
                upload_response = supabase.storage.from_(settings.SUPABASE_BUCKET).upload(direct_path, test_content_2)
                
                if upload_response:
                    public_url = supabase.storage.from_(settings.SUPABASE_BUCKET).get_public_url(direct_path)
                    logger.info(f"✅ 직접 업로드 성공!")
                    logger.info(f"   Public URL: {public_url}")
                    
                    # 7. 메타데이터 저장
                    logger.info("6️⃣ 메타데이터 저장...")
                    
                    attachment_data = {
                        "course_id": "A2025114608241001",
                        "source_type": "test",
                        "source_id": "corrected_direct_test",
                        "file_name": "corrected_direct.txt",
                        "file_size": len(test_content_2),
                        "content_type": "text/plain",
                        "storage_path": public_url,
                        "original_url": "test://corrected_upload"
                    }
                    
                    insert_result = supabase.table('attachments').insert(attachment_data).execute()
                    
                    if insert_result.data:
                        logger.info(f"✅ 메타데이터 저장 성공: ID {insert_result.data[0]['id']}")
                        
                        # 8. 저장된 데이터 조회 확인
                        logger.info("7️⃣ 저장된 데이터 조회...")
                        
                        attachments = supabase.table('attachments').select('*').eq('course_id', 'A2025114608241001').execute()
                        logger.info(f"📎 총 {len(attachments.data)}개의 첨부파일 메타데이터 저장됨")
                        
                        for att in attachments.data[-3:]:  # 최근 3개만 표시
                            logger.info(f"  📄 {att['file_name']} - {att['source_type']} (ID: {att['id']})")
                    else:
                        logger.warning("❌ 메타데이터 저장 실패")
                else:
                    logger.warning("❌ 직접 업로드 실패")
            else:
                logger.warning("❌ FileHandler 업로드 실패")
                
        finally:
            # 임시 파일 삭제
            os.unlink(temp_path)
        
        logger.info("=== ✅ 수정된 Storage 테스트 완료 ===")
        return True
        
    except Exception as e:
        logger.error(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_corrected_storage())
