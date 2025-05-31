#!/usr/bin/env python3
"""
Supabase 저장소 및 첨부파일 업로드 테스트
"""
import asyncio
import sys
import os
import json
from datetime import datetime
sys.path.append('/Users/elaus/PycharmProjects/AutoLMS-R')

from app.core.supabase_client import get_supabase_client
from app.services.file_handler import FileHandler
from app.core.config import settings

async def test_supabase_storage():
    """Supabase 저장소 테스트"""
    print("🗄️ Supabase 저장소 테스트 시작...")
    
    try:
        # Supabase 클라이언트 초기화
        supabase = get_supabase_client()
        print("✅ Supabase 클라이언트 초기화 성공")
        
        # 1. 버킷 확인
        print("📦 버킷 목록 확인...")
        try:
            buckets = supabase.storage.list_buckets()
            print(f"✅ 버킷 목록: {[bucket.name for bucket in buckets]}")
            
            # 기본 버킷 확인
            bucket_name = settings.SUPABASE_BUCKET
            print(f"🎯 대상 버킷: {bucket_name}")
            
        except Exception as e:
            print(f"❌ 버킷 확인 실패: {e}")
            return False
        
        # 2. 테스트 파일 생성
        print("📄 테스트 파일 생성...")
        test_dir = "test_data/upload_test"
        os.makedirs(test_dir, exist_ok=True)
        
        test_file_path = os.path.join(test_dir, "test_document.txt")
        test_content = f"""
AutoLMS-R 첨부파일 업로드 테스트

생성 시간: {datetime.now().isoformat()}
테스트 내용: 이것은 Supabase 저장소 업로드 테스트용 파일입니다.
파일 크기: 작은 텍스트 파일
인코딩: UTF-8

이 파일이 성공적으로 업로드되면 첨부파일 기능이 정상 작동하는 것입니다.
        """.strip()
        
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(test_content)
        
        print(f"✅ 테스트 파일 생성: {test_file_path}")
        
        # 3. 파일 업로드 테스트
        print("⬆️ 파일 업로드 테스트...")
        
        # 파일 핸들러 초기화
        file_handler = FileHandler()
        
        # 업로드할 파일 정보
        file_info = {
            "file_name": "test_document.txt",
            "local_path": test_file_path,
            "course_id": "TEST_COURSE",
            "source_type": "test_upload"
        }
        
        try:
            # 파일 업로드
            storage_url = await file_handler.upload_to_supabase(
                file_info["local_path"],
                file_info["course_id"],
                file_info["source_type"],
                "TEST_ARTICLE_ID"
            )
            
            upload_result = {
                "success": bool(storage_url),
                "storage_path": f"courses/{file_info['course_id']}/{file_info['source_type']}/TEST_ARTICLE_ID/{file_info['file_name']}",
                "public_url": storage_url
            }
            
            if upload_result["success"]:
                print(f"✅ 파일 업로드 성공: {upload_result['storage_path']}")
                print(f"📎 공개 URL: {upload_result.get('public_url', 'N/A')}")
                
                # 4. 업로드된 파일 확인
                print("🔍 업로드된 파일 확인...")
                
                # 파일 목록 확인
                try:
                    files = supabase.storage.from_(bucket_name).list(f"courses/{file_info['course_id']}/{file_info['source_type']}")
                    print(f"📁 업로드된 파일 목록: {[f['name'] for f in files]}")
                    
                    # 파일 다운로드 테스트
                    download_result = supabase.storage.from_(bucket_name).download(upload_result['storage_path'])
                    if download_result:
                        downloaded_content = download_result.decode('utf-8')
                        print(f"📥 다운로드 테스트 성공 (크기: {len(downloaded_content)} 바이트)")
                        
                        # 내용 일부 확인
                        if "AutoLMS-R 첨부파일 업로드 테스트" in downloaded_content:
                            print("✅ 파일 내용 검증 성공")
                        else:
                            print("❌ 파일 내용 검증 실패")
                    else:
                        print("❌ 파일 다운로드 실패")
                        
                except Exception as e:
                    print(f"❌ 파일 확인 실패: {e}")
                
                # 5. 정리 (선택사항)
                print("🧹 테스트 파일 정리...")
                try:
                    supabase.storage.from_(bucket_name).remove([upload_result['storage_path']])
                    print("✅ 테스트 파일 정리 완료")
                except Exception as e:
                    print(f"⚠️ 파일 정리 실패 (무시 가능): {e}")
                
            else:
                print(f"❌ 파일 업로드 실패: {upload_result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ 파일 핸들러 테스트 실패: {e}")
            return False
        
        # 6. 메타데이터 저장 테스트 (테이블 구조가 있다면)
        print("💾 메타데이터 저장 테스트...")
        try:
            # 테스트용 첨부파일 메타데이터
            attachment_data = {
                "file_name": file_info["file_name"],
                "storage_path": upload_result["storage_path"],
                "source_id": "TEST_SOURCE",
                "source_type": file_info["source_type"],
                "course_id": file_info["course_id"],
                "user_id": "TEST_USER",
                "file_size": os.path.getsize(test_file_path),
                "mime_type": "text/plain",
                "uploaded_at": datetime.now().isoformat()
            }
            
            # 실제 테이블이 있다면 저장 시도
            try:
                result = supabase.table("attachments").insert(attachment_data).execute()
                print(f"✅ 메타데이터 저장 성공: {result.data}")
                
                # 저장된 데이터 정리
                if result.data:
                    supabase.table("attachments").delete().eq("source_id", "TEST_SOURCE").execute()
                    print("✅ 테스트 메타데이터 정리 완료")
                    
            except Exception as e:
                print(f"⚠️ 메타데이터 저장 실패 (테이블이 없을 수 있음): {e}")
                
        except Exception as e:
            print(f"❌ 메타데이터 테스트 실패: {e}")
        
        print("🎯 Supabase 저장소 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ Supabase 저장소 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_supabase_storage())
    if success:
        print("🎉 Supabase 저장소 및 첨부파일 테스트 성공!")
    else:
        print("❌ Supabase 저장소 및 첨부파일 테스트 실패")
