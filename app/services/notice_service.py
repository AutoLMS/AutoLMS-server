import logging
from typing import List, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.content_service import ContentService
from app.services.session_service import SessionService
from app.services.parsers.notice_parser import NoticeParser
from app.db.repositories.notice_repository import NoticeRepository
from app.db.repositories.attachment_repository import AttachmentRepository
from app.models.notice import Notice
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

class NoticeService(ContentService[Notice, NoticeParser, NoticeRepository]):
    """공지사항 서비스"""
    
    def __init__(
        self,
        session_service: SessionService,
        notice_parser: NoticeParser,
        notice_repository: NoticeRepository,
        attachment_repository: AttachmentRepository,
        storage_service: StorageService
    ):
        super().__init__(session_service, notice_parser, notice_repository, "notices")
        self.attachment_repository = attachment_repository
        self.storage_service = storage_service
    
    async def get_with_attachments(self, db: AsyncSession, notice_id: str) -> Optional[Dict[str, Any]]:
        """
        첨부파일 정보를 포함한 공지사항 조회
        
        Args:
            db: 데이터베이스 세션
            notice_id: 공지사항 ID
            
        Returns:
            Optional[Dict[str, Any]]: 공지사항 정보
        """
        notice = await self.repository.get_by_id(db, notice_id)
        if not notice:
            return None
            
        # 공지사항 정보를 딕셔너리로 변환
        notice_dict = notice.to_dict() if hasattr(notice, 'to_dict') else vars(notice)
        
        # 첨부파일 조회
        attachments = await self.attachment_repository.get_by_source(db, notice_id, "notices")
        notice_dict["attachments"] = [
            attachment.to_dict() if hasattr(attachment, 'to_dict') else vars(attachment)
            for attachment in attachments
        ]
        
        return notice_dict
    
    async def refresh_all(
        self, 
        db: AsyncSession, 
        course_id: str, 
        user_id: str, 
        auto_download: bool = False
    ) -> Dict[str, Any]:
        """
        특정 강의의 공지사항 새로고침
        
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
            
            # 2. 공지사항 목록 페이지 접근
            base_url = "https://eclass.seoultech.ac.kr"
            notice_url = f"{base_url}/notice/notice_list.jsp?ud={user_id}&ky={course_id}"
            
            data = {
                'start': '1',
                'display': '100',  # 한 번에 가져올 개수
                'SCH_VALUE': '',
                'ud': user_id,
                'ky': course_id,
                'encoding': 'utf-8'
            }
            
            response = await eclass_session.post(notice_url, data=data)
            if not response:
                logger.error("공지사항 목록 요청 실패")
                result["errors"] += 1
                return result
            
            # 3. 목록 파싱
            notices = self.parser.parse_list(response.text)
            if not notices:
                logger.info(f"강의 {course_id}의 공지사항이 없습니다.")
                return result
            
            # 4. 기존 공지사항 조회
            existing_notices = await self.repository.get_by_course_id(db, course_id)
            existing_article_ids = {notice.article_id for notice in existing_notices}
            
            # 5. 각 공지사항 처리
            for notice in notices:
                result["count"] += 1
                article_id = notice.get("article_id")
                
                if not article_id:
                    result["errors"] += 1
                    continue
                
                try:
                    # 이미 존재하는 공지사항 건너뛰기
                    if article_id in existing_article_ids:
                        continue
                    
                    # 상세 페이지 요청
                    detail_url = notice.get("url")
                    detail_response = await eclass_session.get(detail_url)
                    if not detail_response:
                        logger.error(f"공지사항 상세 정보 요청 실패: {article_id}")
                        result["errors"] += 1
                        continue
                    
                    # 상세 정보 파싱
                    notice_detail = self.parser.parse_detail(detail_response.text)
                    notice.update(notice_detail)
                    
                    # DB 저장
                    notice_data = {
                        'article_id': article_id,
                        'course_id': course_id,
                        'title': notice.get('title'),
                        'content': notice_detail.get('content'),
                        'author': notice.get('author'),
                        'date': notice.get('date'),
                        'views': notice.get('views'),
                    }
                    
                    created_notice = await self.repository.create(db, notice_data)
                    result["new"] += 1
                    
                    # 첨부파일 처리
                    if auto_download and notice_detail.get("attachments"):
                        for attachment in notice_detail.get("attachments", []):
                            try:
                                # 파일 다운로드 및 스토리지 업로드
                                file_data = await eclass_session.download_file(attachment["original_url"])
                                if not file_data:
                                    logger.error(f"첨부파일 다운로드 실패: {attachment['file_name']}")
                                    continue
                                
                                # 스토리지에 업로드
                                storage_path = await self.storage_service.upload_file(
                                    file_data,
                                    attachment["file_name"],
                                    course_id,
                                    "notices"
                                )
                                
                                # 첨부파일 메타데이터 저장
                                attachment_data = {
                                    "file_name": attachment["file_name"],
                                    "original_url": attachment["original_url"],
                                    "storage_path": storage_path,
                                    "source_id": created_notice.id,
                                    "source_type": "notices",
                                    "course_id": course_id,
                                }
                                await self.attachment_repository.create(db, attachment_data)
                                
                            except Exception as e:
                                logger.error(f"첨부파일 처리 중 오류: {str(e)}")
                                continue
                    
                except Exception as e:
                    logger.error(f"공지사항 {article_id} 처리 중 오류: {str(e)}")
                    result["errors"] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"공지사항 크롤링 중 오류 발생: {str(e)}")
            result["errors"] += 1
            return result
