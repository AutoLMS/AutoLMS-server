import logging
from typing import List, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.content_service import ContentService
from app.services.core.session_service import SessionService
from app.services.parsers.material_parser import MaterialParser
from app.services.storage.storage_service import StorageService
from app.db.repositories.material_repository import MaterialRepository
from app.db.repositories.attachment_repository import AttachmentRepository
from app.models.material import Material

logger = logging.getLogger(__name__)

class MaterialService(ContentService[Material, MaterialParser, MaterialRepository]):
    """강의자료 서비스"""
    
    def __init__(
        self,
        session_service: SessionService,
        material_parser: MaterialParser,
        material_repository: MaterialRepository,
        attachment_repository: AttachmentRepository,
        storage_service: StorageService
    ):
        super().__init__(
            session_service,
            material_parser,
            material_repository,
            attachment_repository,
            storage_service,
            "materials"
        )
    
    async def refresh_all(
        self, 
        db: AsyncSession, 
        course_id: str, 
        user_id: str, 
        auto_download: bool = False
    ) -> Dict[str, Any]:
        """
        특정 강의의 강의자료 새로고침
        
        Args:
            db: 데이터베이스 세션
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
            base_url = "https://eclass.seoultech.ac.kr"
            material_url = f"{base_url}/lecture_material/lecture_material_list.jsp?ud={user_id}&ky={course_id}"
            
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
            existing_materials = await self.repository.get_by_course_id(db, course_id)
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
                    
                    created_material = await self.repository.create(db, material_data)
                    result["new"] += 1
                    
                    # 첨부파일 처리
                    if auto_download and material.get("attachments"):
                        attachment_count = await self._process_attachments(
                            db,
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
