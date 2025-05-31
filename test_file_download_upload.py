#!/usr/bin/env python3
"""
실제 강의자료 파일 다운로드 + Supabase Storage 업로드 테스트
"""
import asyncio
import logging
from app.core.config import settings
from app.core.supabase_client import get_supabase_client
from app.services.eclass_service import EclassService
from app.services.file_handler import FileHandler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_file_download_and_upload():
    """실제 파일 다운로드 + Supabase 업로드 테스트"""
    try:
        logger.info("=== 실제 파일 다운로드 + Supabase 업로드 테스트 ===")
        
        # 1. Supabase 연결 확인
        logger.info("1️⃣ Supabase Storage 연결 확인...")
        supabase = get_supabase_client()
        
        # Storage bucket 확인
        buckets = supabase.storage.list_buckets()
        logger.info(f"✅ 사용 가능한 Storage buckets: {[b.name for b in buckets]}")
        
        # 2. eClass 로그인 및 서비스 초기화
        logger.info("2️⃣ eClass 서비스 초기화...")
        file_handler = FileHandler()
        eclass_service = EclassService(file_handler=file_handler)
        
        await eclass_service.login(settings.ECLASS_USERNAME, settings.ECLASS_PASSWORD)
        logger.info("✅ eClass 로그인 성공")
        
        # 3. 실제 강의에서 강의자료 크롤링 (auto_download=True)
        logger.info("3️⃣ 실제 강의자료 크롤링 + 파일 다운로드 시작...")
        
        # 테스트용 강의 ID (실제 데이터가 있는 강의)
        test_course_id = "A2025114608241001"  # Capstone Design I
        test_user_id = "432b5cc0-c820-4f93-b007-d8b5d659b32e"
        
        # Supabase 클라이언트를 사용한 DB 접근 (SQLAlchemy 대신)
        logger.info(f"강의 {test_course_id}의 강의자료 크롤링 중...")
        
        # 실제 강의자료 페이지 접근
        materials_url = f"https://eclass.seoultech.ac.kr/ilos/st/course/lecture_material_list.acl"
        
        # eClass 세션을 통해 강의자료 목록 가져오기
        data = {
            'start': '1',
            'display': '50',
            'SCH_VALUE': '',
            'ud': test_user_id,
            'ky': test_course_id,
            'encoding': 'utf-8'
        }
        
        response = await eclass_service.session.post(materials_url, data=data)
        
        if response and response.text:
            logger.info("✅ 강의자료 목록 페이지 접근 성공")
            
            # 강의자료 파싱
            materials = eclass_service.parser.parse_material_list(response.text)
            logger.info(f"📚 발견된 강의자료 수: {len(materials)}")
            
            if materials:
                # 첫 번째 강의자료의 상세 정보 가져오기
                first_material = materials[0]
                logger.info(f"📄 첫 번째 강의자료: {first_material.get('title')}")
                
                # 상세 페이지 접근
                detail_response = await eclass_service.session.get(first_material["url"])
                
                if detail_response:
                    # 상세 정보 파싱 (첨부파일 포함)
                    material_detail = await eclass_service.parser.parse_material_detail(
                        eclass_service.session, detail_response.text, test_course_id
                    )
                    
                    logger.info(f"📎 첨부파일 수: {len(material_detail.get('attachments', []))}")
                    
                    # 첨부파일이 있는 경우 다운로드 테스트
                    if material_detail.get('attachments'):
                        logger.info("4️⃣ 첨부파일 다운로드 + Supabase 업로드 시작...")
                        
                        # 첨부파일 다운로드 및 업로드
                        attachment_results = await file_handler.download_attachments(
                            eclass_service.session, 
                            {**first_material, **material_detail}, 
                            test_course_id
                        )
                        
                        logger.info(f"📊 다운로드 결과: {len(attachment_results)}개 처리")
                        
                        # 결과 출력
                        for i, result in enumerate(attachment_results):
                            if result.get('success'):
                                logger.info(f"  ✅ {i+1}. {result['file_name']}")
                                logger.info(f"     저장 경로: {result['storage_path']}")
                                logger.info(f"     원본 URL: {result['original_url']}")
                                
                                # Supabase에 메타데이터 저장
                                attachment_data = {
                                    "course_id": test_course_id,
                                    "source_type": "material",
                                    "source_id": first_material.get('article_id', 'test'),
                                    "file_name": result['file_name'],
                                    "file_size": 0,  # 실제 구현에서는 파일 크기 계산
                                    "content_type": "application/octet-stream",
                                    "storage_path": result['storage_path'],
                                    "original_url": result['original_url']
                                }
                                
                                # Supabase attachments 테이블에 저장
                                insert_result = supabase.table('attachments').insert(attachment_data).execute()
                                
                                if insert_result.data:
                                    logger.info(f"     ✅ DB 메타데이터 저장 완료: ID {insert_result.data[0]['id']}")
                                else:
                                    logger.warning(f"     ⚠️ DB 메타데이터 저장 실패")
                            else:
                                logger.warning(f"  ❌ {i+1}. 다운로드 실패: {result.get('error', '알 수 없는 오류')}")
                        
                        # 5. Supabase Storage 파일 목록 확인
                        logger.info("5️⃣ Supabase Storage 파일 확인...")
                        
                        try:
                            # 해당 강의의 파일 목록 조회
                            files = supabase.storage.from_('autolms').list(f'courses/{test_course_id}/')
                            logger.info(f"📁 Storage에 저장된 파일 수: {len(files) if files else 0}")
                            
                            if files:
                                for file in files[:3]:  # 처음 3개만 표시
                                    logger.info(f"  📄 {file.get('name', 'Unknown')}")
                        except Exception as e:
                            logger.warning(f"Storage 파일 목록 조회 실패: {e}")
                        
                    else:
                        logger.info("📎 이 강의자료에는 첨부파일이 없습니다.")
                        
                        # 테스트용 파일 생성 및 업로드
                        logger.info("🧪 테스트용 파일 생성 및 업로드...")
                        
                        test_content = f"""테스트 파일입니다.
강의: {first_material.get('title', 'Unknown')}
생성 시간: {first_material.get('date', 'Unknown')}
테스트 데이터입니다.""".encode('utf-8')
                        
                        # 임시 파일 저장
                        import tempfile
                        import os
                        
                        with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as temp_file:
                            temp_file.write(test_content)
                            temp_path = temp_file.name
                        
                        try:
                            # Supabase에 업로드
                            storage_url = await file_handler.upload_to_supabase(
                                temp_path, 
                                test_course_id, 
                                'material', 
                                first_material.get('article_id', 'test')
                            )
                            
                            if storage_url:
                                logger.info(f"✅ 테스트 파일 업로드 성공: {storage_url}")
                            else:
                                logger.warning("❌ 테스트 파일 업로드 실패")
                        finally:
                            # 임시 파일 삭제
                            os.unlink(temp_path)
            else:
                logger.info("📚 이 강의에는 강의자료가 없습니다.")
        else:
            logger.warning("⚠️ 강의자료 목록 페이지 접근 실패")
        
        logger.info("=== ✅ 파일 다운로드 + 업로드 테스트 완료 ===")
        return True
        
    except Exception as e:
        logger.error(f"❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_file_download_and_upload())
