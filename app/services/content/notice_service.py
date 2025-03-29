import logging
from typing import List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.content.content_service import ContentService
from app.services.session import EclassSessionManager
from app.services.parsers.notice_parser import NoticeParser
from app.services.storage.storage_service import StorageService
from app.db.repositories.notice_repository import NoticeRepository
from app.db.repositories.attachment_repository import AttachmentRepository
from app.models.notice import Notice

logger = logging.getLogger(__name__)

class NoticeService(ContentService[Notice, NoticeParser, NoticeRepository]):
    """공지사항 서비스"""
    
    def __init__(
        self,
        eclass_session: EclassSessionManager,
        notice_parser: NoticeParser,
        notice_repository: NoticeRepository,
        attachment_repository: AttachmentRepository,
        storage_service: StorageService
    ):
        super().__init__(
            eclass_session,
            notice_parser,
            notice_repository,
            content_type="notices"
        )
    
    async def get_notices(self, user_id: str, course_id: str, db: AsyncSession) -> List[Notice]:
        """
        특정 강의의 공지사항 목록 조회
        
        Args:
            user_id: 사용자 ID
            course_id: 강의 ID
            db: 데이터베이스 세션
            
        Returns:
            List[Notice]: 공지사항 목록
        """
        try:
            logger.info(f"사용자 {user_id}의 강의 {course_id} 공지사항 조회")
            
            # 1. 강의 접근 권한 확인
            from app.core.security import verify_course_access
            await verify_course_access(user_id, course_id, db)
            
            # 2. 데이터베이스에서 공지사항 조회
            notices = await self.repository.get_by_course_id(db, course_id)
            
            # 3. 공지사항이 없으면 새로고침 시도
            if not notices:
                logger.info(f"강의 {course_id}의 공지사항이 없습니다. 새로고침을 시도합니다.")
                result = await self.refresh_all(db, course_id, user_id)
                if result["new"] > 0:
                    # 새로고침 후 다시 조회
                    notices = await self.repository.get_by_course_id(db, course_id)
            
            # 4. 공지사항 목록 반환
            logger.info(f"강의 {course_id}의 공지사항 {len(notices)}개 반환")
            return list(notices)
            
        except Exception as e:
            logger.error(f"공지사항 조회 중 오류: {str(e)}")
            return []
    
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
                    
                    # 상세 정보 파싱 (AJAX 요청 포함)
                    notice_detail = await self.parser.parse_detail_with_attachments(
                        eclass_session, 
                        detail_response.text, 
                        course_id
                    )
                    
                    # 기본 필드 정보 병합
                    notice.update(notice_detail)
                    
                    # DB 저장
                    notice_data = {
                        'article_id': article_id,
                        'course_id': course_id,
                        'title': notice.get('title'),
                        'content': notice_detail.get('content'),
                        'content_html': notice_detail.get('content_html', ''),
                        'author': notice.get('author'),
                        'date': notice.get('date'),
                        'views': notice.get('views'),
                    }
                    
                    created_notice = await self.repository.create(db, notice_data)
                    result["new"] += 1
                    
                    # 첨부파일 처리
                    if auto_download and notice.get("attachments"):
                        attachment_count = await self._process_attachments(
                            db,
                            eclass_session,
                            notice["attachments"],
                            created_notice.id,
                            course_id
                        )
                        logger.info(f"처리된 첨부파일 수: {attachment_count}")
                    
                except Exception as e:
                    logger.error(f"공지사항 {article_id} 처리 중 오류: {str(e)}")
                    result["errors"] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"공지사항 크롤링 중 오류 발생: {str(e)}")
            result["errors"] += 1
            return result

    async def _process_attachments(
            self,
            db: AsyncSession,
            eclass_session,
            attachments: List[Dict[str, Any]],
            source_id: int,
            course_id: str
    ) -> int:
        """
        첨부파일 처리 및 저장

        Args:
            db: 데이터베이스 세션
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
                await self.attachment_repository.create(db, attachment_data)
                count += 1
                logger.info(f"첨부파일 메타데이터 저장 완료: {file_name}")

            except Exception as e:
                logger.error(f"첨부파일 '{attachment.get('file_name', '알 수 없음')}' 처리 중 오류: {str(e)}")

        return count