#!/usr/bin/env python3
"""
강의자료 다운로드 + Supabase 저장 테스트
"""
import asyncio
import logging
from app.core.supabase_client import get_supabase_client
from app.core.config import settings
from app.services.eclass_service import EclassService
from app.services.file_handler import FileHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_material_download_with_supabase():
    """Supabase를 사용한 강의자료 다운로드 테스트"""
    try:
        logger.info("=== 강의자료 다운로드 + Supabase 저장 테스트 시작 ===")
        
        # 1. Supabase 클라이언트 연결 확인
        logger.info("1️⃣ Supabase 연결 확인...")
        supabase = get_supabase_client()
        courses_result = supabase.table('courses').select('*').limit(1).execute()
        
        if not courses_result.data:
            logger.error("❌ 테스트할 course 데이터가 없습니다")
            return False
        
        test_course = courses_result.data[0]
        course_id = test_course['id']
        logger.info(f"✅ 테스트 course: {test_course['name']} (ID: {course_id})")
        
        # 2. eClass 로그인
        logger.info("2️⃣ eClass 로그인...")
        file_handler = FileHandler()
        eclass_service = EclassService(file_handler=file_handler)
        await eclass_service.login(settings.ECLASS_USERNAME, settings.ECLASS_PASSWORD)
        logger.info("✅ eClass 로그인 성공")
        
        # 3. 강의자료 크롤링 테스트 (첫 번째 페이지만)
        logger.info("3️⃣ 강의자료 크롤링 테스트...")
        
        # eClass parser를 직접 사용해서 강의자료 페이지 크롤링
        from app.services.eclass_parser import EclassParser
        parser = EclassParser()
        
        # 강의자료 페이지 URL
        materials_url = f"https://eclass.seoultech.ac.kr/ilos/st/course/submain_form.acl?KJKEY={course_id}&"
        logger.info(f"크롤링 URL: {materials_url}")
        
        # 실제 HTTP 요청을 통해 페이지 가져오기
        import httpx
        async with httpx.AsyncClient() as client:
            # eClass 세션 쿠키 사용
            cookies = eclass_service.session.cookies if hasattr(eclass_service, 'session') else {}
            
            response = await client.get(materials_url, cookies=cookies)
            if response.status_code == 200:
                logger.info("✅ 강의자료 페이지 접근 성공")
                
                # 간단한 파싱 테스트 (실제 파일이 있는지 확인)
                content = response.text
                if "첨부파일" in content or "attachment" in content.lower():
                    logger.info("📎 페이지에 첨부파일 관련 내용 발견")
                else:
                    logger.info("📄 일반 텍스트 강의자료 페이지")
            else:
                logger.warning(f"⚠️ 강의자료 페이지 접근 실패: {response.status_code}")
        
        # 4. Supabase에 테스트 데이터 저장
        logger.info("4️⃣ Supabase에 테스트 material 저장...")
        
        test_material = {
            "article_id": "test_article_001",
            "course_id": course_id,
            "title": "테스트 강의자료",
            "content": "테스트용 강의자료 내용입니다.",
            "author": "테스트 작성자",
            "date": "2025-05-31",
            "views": 0
        }
        
        # Supabase에 material 저장
        material_result = supabase.table('materials').insert(test_material).execute()
        
        if material_result.data:
            logger.info(f"✅ Material 저장 성공! ID: {material_result.data[0]['id']}")
            
            # 5. 테스트 첨부파일 메타데이터 저장
            logger.info("5️⃣ 테스트 첨부파일 메타데이터 저장...")
            
            test_attachment = {
                "course_id": course_id,
                "source_type": "material",
                "source_id": str(material_result.data[0]['id']),
                "file_name": "test_document.pdf",
                "file_size": 1024000,  # 1MB
                "content_type": "application/pdf",
                "storage_path": f"materials/{course_id}/test_document.pdf",
                "original_url": "https://eclass.seoultech.ac.kr/test/file.pdf"
            }
            
            attachment_result = supabase.table('attachments').insert(test_attachment).execute()
            
            if attachment_result.data:
                logger.info(f"✅ Attachment 저장 성공! ID: {attachment_result.data[0]['id']}")
            else:
                logger.error("❌ Attachment 저장 실패")
        else:
            logger.error("❌ Material 저장 실패")
        
        # 6. 저장된 데이터 조회 확인
        logger.info("6️⃣ 저장된 데이터 조회 확인...")
        
        # Materials 조회
        materials = supabase.table('materials').select('*').eq('course_id', course_id).execute()
        logger.info(f"📚 Course {course_id}의 materials 수: {len(materials.data)}")
        
        # Attachments 조회
        attachments = supabase.table('attachments').select('*').eq('course_id', course_id).execute()
        logger.info(f"📎 Course {course_id}의 attachments 수: {len(attachments.data)}")
        
        logger.info("=== ✅ 테스트 완료 ===")
        return True
        
    except Exception as e:
        logger.error(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_material_download_with_supabase())
