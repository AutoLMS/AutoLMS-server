#!/usr/bin/env python3
"""
Supabase Storage 설정 및 테스트 파일 업로드
"""
import asyncio
import logging
import tempfile
import os
from app.core.supabase_client import get_supabase_client
from app.services.file_handler import FileHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def setup_supabase_storage():
    """Supabase Storage 설정 및 테스트"""
    try:
        logger.info("=== Supabase Storage 설정 및 테스트 ===")
        
        # 1. Supabase 클라이언트 초기화
        supabase = get_supabase_client()
        
        # 2. 기존 버킷 확인
        logger.info("1️⃣ 기존 Storage bucket 확인...")
        buckets = supabase.storage.list_buckets()
        logger.info(f"기존 buckets: {[b.name for b in buckets]}")
        
        # 3. autolms bucket 생성 (이미 존재하면 에러 무시)
        logger.info("2️⃣ autolms bucket 생성 시도...")
        try:
            create_result = supabase.storage.create_bucket('autolms')
            logger.info(f"✅ autolms bucket 생성 성공: {create_result}")
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info("ℹ️ autolms bucket이 이미 존재합니다.")
            else:
                logger.warning(f"Bucket 생성 실패: {e}")
        
        # 4. 다시 bucket 목록 확인
        buckets = supabase.storage.list_buckets()
        logger.info(f"업데이트된 buckets: {[b.name for b in buckets]}")
        
        # 5. 테스트 파일 생성
        logger.info("3️⃣ 테스트 파일 생성...")
        test_content = """# AutoLMS 테스트 파일

이것은 Supabase Storage 업로드 테스트를 위한 파일입니다.

## 파일 정보
- 생성 시간: 2025-05-31
- 목적: 파일 업로드 기능 테스트
- 강의: Capstone Design I (A2025114608241001)

## 테스트 내용
1. 파일 생성 ✅
2. Supabase Storage 업로드 ⏳
3. URL 접근 테스트 ⏳
4. 메타데이터 저장 ⏳

테스트 완료!
""".encode('utf-8')
        
        # 6. 임시 파일 생성 및 업로드 테스트
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as temp_file:
            temp_file.write(test_content)
            temp_path = temp_file.name
            temp_filename = 'autolms_test_file.txt'
        
        try:
            logger.info("4️⃣ FileHandler를 통한 Supabase 업로드 테스트...")
            
            # FileHandler 사용
            file_handler = FileHandler()
            
            # 직접 업로드 테스트
            storage_url = await file_handler.upload_to_supabase(
                temp_path,
                'A2025114608241001',  # course_id
                'test',               # source_type
                'test_article_001'    # article_id
            )
            
            if storage_url:
                logger.info(f"✅ 파일 업로드 성공!")
                logger.info(f"   Storage URL: {storage_url}")
                
                # 7. 직접 Supabase Storage API 테스트
                logger.info("5️⃣ 직접 Storage API 테스트...")
                
                # 파일 목록 확인
                try:
                    files = supabase.storage.from_('autolms').list('courses/A2025114608241001/')
                    logger.info(f"📁 저장된 파일 목록: {len(files) if files else 0}개")
                    
                    if files:
                        for file in files:
                            logger.info(f"  📄 {file.get('name', 'Unknown')} ({file.get('size', 0)} bytes)")
                except Exception as e:
                    logger.warning(f"파일 목록 조회 실패: {e}")
                
                # 8. 추가 테스트 파일 직접 업로드
                logger.info("6️⃣ 추가 직접 업로드 테스트...")
                
                test_content_2 = b"Direct upload test content for AutoLMS"
                storage_path = "courses/A2025114608241001/test/direct_upload/test_direct.txt"
                
                try:
                    upload_response = supabase.storage.from_('autolms').upload(storage_path, test_content_2)
                    
                    if upload_response:
                        logger.info("✅ 직접 업로드 성공!")
                        
                        # Public URL 가져오기
                        public_url = supabase.storage.from_('autolms').get_public_url(storage_path)
                        logger.info(f"   Public URL: {public_url}")
                        
                        # 9. 메타데이터 저장 테스트
                        logger.info("7️⃣ 메타데이터 저장 테스트...")
                        
                        attachment_data = {
                            "course_id": "A2025114608241001",
                            "source_type": "test",
                            "source_id": "direct_upload_test",
                            "file_name": "test_direct.txt",
                            "file_size": len(test_content_2),
                            "content_type": "text/plain",
                            "storage_path": public_url,
                            "original_url": "test://direct_upload"
                        }
                        
                        # DB에 저장
                        insert_result = supabase.table('attachments').insert(attachment_data).execute()
                        
                        if insert_result.data:
                            logger.info(f"✅ 메타데이터 저장 성공: ID {insert_result.data[0]['id']}")
                        else:
                            logger.warning("❌ 메타데이터 저장 실패")
                    else:
                        logger.warning("❌ 직접 업로드 실패")
                        
                except Exception as e:
                    logger.error(f"직접 업로드 중 오류: {e}")
            else:
                logger.warning("❌ FileHandler 업로드 실패")
                
        finally:
            # 임시 파일 삭제
            os.unlink(temp_path)
        
        logger.info("=== ✅ Supabase Storage 테스트 완료 ===")
        return True
        
    except Exception as e:
        logger.error(f"❌ Storage 설정 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(setup_supabase_storage())
