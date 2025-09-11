import logging
from typing import Dict, Any, List

from app.services.auth_service import AuthService
from app.services.base_service import BaseService
from app.services.session import EclassSessionManager
from app.services.parsers.material_parser import MaterialParser
from app.services.storage.storage_service import StorageService
from app.db.repositories.material_repository import MaterialRepository
from app.db.repositories.attachment_repository import AttachmentRepository

logger = logging.getLogger(__name__)

class MaterialService(BaseService):
    """강의자료 서비스"""
    def __init__(
            self,
            eclass_session: EclassSessionManager,
            material_parser: MaterialParser,
            material_repository: MaterialRepository,
            attachment_repository: AttachmentRepository,
            storage_service: StorageService,
            auth_service: AuthService
    ):
        # BaseService에는 __init__이 없으므로 super() 호출 제거
        # 모든 필요한 속성들을 직접 설정
        self.session_service = eclass_session
        self.parser = material_parser
        self.repository = material_repository
        self.auth_service = auth_service
        self.attachment_repository = attachment_repository
        self.storage_service = storage_service
    
    async def initialize(self) -> None:
        """서비스 초기화"""
        logger.info("MaterialService 초기화 시작")
        
        # 필요한 초기화 작업 수행
        if hasattr(self.storage_service, 'initialize'):
            await self.storage_service.initialize()
        
        logger.info("MaterialService 초기화 완료")
    
    async def close(self) -> None:
        """서비스 리소스 정리"""
        logger.info("MaterialService 리소스 정리 시작")
        
        # 필요한 정리 작업 수행
        if hasattr(self.storage_service, 'close'):
            await self.storage_service.close()
        
        logger.info("MaterialService 리소스 정리 완료")

    async def refresh_all(
        self, 
        course_id: str, 
        user_id: str, 
        auto_download: bool = False
    ) -> Dict[str, Any]:
        """
        특정 강의의 강의자료 새로고침
        
        Args:
            course_id: 강의 ID
            user_id: 사용자 ID
            auto_download: 첨부파일 자동 다운로드 여부
            
        Returns:
            Dict[str, Any]: 새로고침 결과
        """
        result = {"count": 0, "new": 0, "errors": 0}
        
        try:
            # 1. 세션 가져오기
            eclass_session = await self.session_service.get_session(user_id)
            if not eclass_session:
                logger.error(f"이클래스 세션을 가져올 수 없음")
                result["errors"] += 1
                return result
            
            # 2. 강의자료 목록 페이지 접근
            # 이클래스 ID 조회
            eclass_credentials = await self.auth_service.get_user_eclass_credentials(user_id)
            if not eclass_credentials or not eclass_credentials.get("username"):
                logger.error(f"사용자 {user_id}의 이클래스 계정 정보를 찾을 수 없음")
                return None

            eclass_id = eclass_credentials["username"]

            base_url = "https://eclass.seoultech.ac.kr"
            material_url = f"{base_url}/lecture_material/lecture_material_list.jsp?ud={eclass_id}&ky={course_id}"
            
            response = await eclass_session.get(material_url)
            if not response:
                logger.error("강의자료 목록 요청 실패")
                result["errors"] += 1
                return result
            
            # 3. 목록 파싱
            materials = self.parser.parse_list(response.text)
            if not materials:
                logger.info(f"강의 {course_id}의 강의자료가 없습니다.")
                return result
            
            # 4. 기존 강의자료 조회
            existing_materials = await self.repository.get_by_course_id(course_id)
            existing_article_ids = {material.article_id for material in existing_materials}
            
            # 5. 각 강의자료 처리
            for material in materials:
                result["count"] += 1
                article_id = material.get("article_id")
                
                if not article_id:
                    result["errors"] += 1
                    continue
                
                try:
                    # 이미 존재하는 강의자료 건너뛰기
                    if article_id in existing_article_ids:
                        continue
                    
                    # 상세 페이지 요청
                    detail_url = material.get("url")
                    detail_response = await eclass_session.get(detail_url)
                    if not detail_response:
                        logger.error(f"강의자료 상세 정보 요청 실패: {article_id}")
                        result["errors"] += 1
                        continue
                    
                    # 상세 정보 파싱 (AJAX 요청 포함)
                    material_detail = await self.parser.parse_detail_with_attachments(
                        eclass_session, 
                        detail_response.text, 
                        course_id
                    )
                    
                    # 기본 필드 정보 병합
                    material.update(material_detail)
                    
                    # DB 저장
                    material_data = {
                        'article_id': article_id,
                        'course_id': course_id,
                        'title': material.get('title'),
                        'content': material_detail.get('content', ''),
                        'content_html': material_detail.get('content_html', ''),
                        'author': material.get('author'),
                        'date': material.get('date'),
                        'views': material.get('views'),
                        'video_url': material_detail.get('video_url', '')
                    }
                    
                    created_material = await self.repository.create(material_data)
                    result["new"] += 1
                    
                    # 첨부파일 처리
                    if auto_download and material.get("attachments"):
                        attachment_count = await self._process_attachments(
                            eclass_session,
                            material["attachments"],
                            created_material.id,
                            course_id
                        )
                        logger.info(f"처리된 첨부파일 수: {attachment_count}")
                    
                except Exception as e:
                    logger.error(f"강의자료 {article_id} 처리 중 오류: {str(e)}")
                    result["errors"] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"강의자료 크롤링 중 오류 발생: {str(e)}")
            result["errors"] += 1
            return result

    async def _process_attachments(
            self,
            eclass_session,
            attachments: List[Dict[str, Any]],
            source_id: int,
            course_id: str
    ) -> int:
        """
        첨부파일 처리 및 저장

        Args:
            eclass_session: 이클래스 세션 객체
            attachments: 첨부파일 정보 목록
            source_id: 소스(강의자료) ID
            course_id: 강의 ID

        Returns:
            int: 처리된 첨부파일 수
        """
        count = 0

        # 첨부파일 저장소와 스토리지 서비스가 클래스에 없으면 추가
        if not hasattr(self, 'attachment_repository'):
            from app.db.repositories.attachment_repository import AttachmentRepository
            self.attachment_repository = AttachmentRepository()

        if not hasattr(self, 'storage_service'):
            from app.services.storage.storage_service import StorageService
            self.storage_service = StorageService()

        # 각 첨부파일 처리
        for attachment in attachments:
            try:
                # 첨부파일 정보 로깅
                file_name = attachment.get("file_name", "")
                original_url = attachment.get("original_url", "")

                if not file_name or not original_url:
                    logger.warning(f"첨부파일 정보 부족: {attachment}")
                    continue

                logger.info(f"첨부파일 처리 시작: {file_name}")

                # 이클래스에서 파일 다운로드
                try:
                    # GET 요청으로 파일 다운로드
                    download_response = await eclass_session.get(original_url)
                    if not download_response:
                        logger.error(f"파일 다운로드 실패: {file_name}")
                        continue

                    # 파일 내용 추출
                    file_content = download_response.content
                    file_size = len(file_content)

                    if file_size == 0:
                        logger.warning(f"다운로드한 파일 크기가 0입니다: {file_name}")
                        continue

                    logger.info(f"파일 다운로드 완료: {file_name} ({file_size} 바이트)")
                except Exception as e:
                    logger.error(f"파일 다운로드 중 오류: {str(e)}")
                    continue

                # 스토리지에 업로드
                storage_path = await self.storage_service.upload_file(
                    file_content,
                    file_name,
                    course_id,
                    "materials"  # 콘텐츠 타입
                )

                if not storage_path:
                    logger.error(f"파일 업로드 실패: {file_name}")
                    continue

                logger.info(f"파일 업로드 완료: {storage_path}")

                # 첨부파일 메타데이터 저장
                attachment_data = {
                    "source_type": "materials",
                    "source_id": str(source_id),
                    "file_name": file_name,
                    "file_size": file_size,
                    "content_type": attachment.get("content_type", ""),
                    "storage_path": storage_path,
                    "original_url": original_url,
                    "course_id": course_id
                }

                # 데이터베이스에 저장
                await self.attachment_repository.upsert(attachment_data)
                count += 1
                logger.info(f"첨부파일 메타데이터 저장 완료: {file_name}")

            except Exception as e:
                logger.error(f"첨부파일 '{attachment.get('file_name', '알 수 없음')}' 처리 중 오류: {str(e)}")

        return count