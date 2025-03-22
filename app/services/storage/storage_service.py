import logging
import os
import hashlib
from typing import Dict, Any, Optional, BinaryIO, Union, List
from pathlib import Path

import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.base_service import BaseService
from app.core.config import settings
from app.models.attachment import Attachment
from app.core.security import verify_attachment_access

logger = logging.getLogger(__name__)

class StorageService(BaseService):
    """파일 스토리지 서비스"""
    
    def __init__(self):
        self.local_download_dir = settings.DOWNLOAD_DIR
        logger.info("StorageService 초기화 완료")
        
        # Supabase 클라이언트 초기화 (설정된 경우)
        self.supabase = None
        self.bucket_name = settings.SUPABASE_BUCKET
        
        if settings.SUPABASE_URL and settings.SUPABASE_KEY:
            try:
                from supabase import create_client
                self.supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
                logger.info("Supabase 스토리지 클라이언트 초기화 완료")
            except Exception as e:
                logger.error(f"Supabase 클라이언트 초기화 중 오류 발생: {str(e)}")
    
    async def initialize(self) -> None:
        """서비스 초기화"""
        logger.info("StorageService 시작")
        # 로컬 디렉토리 생성
        os.makedirs(self.local_download_dir, exist_ok=True)
    
    async def close(self) -> None:
        """서비스 리소스 정리"""
        logger.info("StorageService 종료")
        pass
    
    async def upload_file(
        self, 
        file_data: Union[bytes, BinaryIO], 
        filename: str, 
        course_id: str, 
        content_type: str
    ) -> str:
        """
        파일을 스토리지에 업로드
        
        Args:
            file_data: 파일 데이터 (바이트)
            filename: 파일 이름
            course_id: 강의 ID
            content_type: 콘텐츠 타입 ('notices', 'materials', 'assignments' 등)
            
        Returns:
            str: 스토리지 경로
        """
        try:
            # 파일 경로 생성
            file_path = f"{course_id}/{content_type}/{filename}"
            
            # Supabase Storage에 업로드
            if self.supabase:
                try:
                    storage = self.supabase.storage.from_(self.bucket_name)
                    
                    # 바이트 데이터인 경우
                    if isinstance(file_data, bytes):
                        response = storage.upload(file_path, file_data)
                    # 파일 객체인 경우
                    else:
                        file_data.seek(0)  # 파일 포인터를 처음으로 이동
                        response = storage.upload(file_path, file_data.read())
                        
                    logger.info(f"파일 '{filename}' 업로드 완료: {file_path}")
                    return file_path
                except Exception as e:
                    logger.error(f"Supabase 업로드 중 오류: {str(e)}")
                    # 실패 시 로컬에 저장 시도
            
            # Supabase가 설정되지 않은 경우나 업로드 실패 시 로컬에 저장
            return await self._save_file_locally(file_data, course_id, content_type, filename)
            
        except Exception as e:
            logger.error(f"파일 '{filename}' 업로드 중 오류 발생: {str(e)}")
            # 실패 시 로컬에 저장 시도
            return await self._save_file_locally(file_data, course_id, content_type, filename)
    
    async def _save_file_locally(
        self, 
        file_data: Union[bytes, BinaryIO], 
        course_id: str, 
        content_type: str, 
        filename: str
    ) -> str:
        """
        파일을 로컬에 저장
        
        Args:
            file_data: 파일 데이터
            course_id: 강의 ID
            content_type: 콘텐츠 타입
            filename: 파일 이름
            
        Returns:
            str: 로컬 파일 경로
        """
        try:
            # 저장 디렉토리 생성
            save_dir = os.path.join(self.local_download_dir, course_id, content_type)
            os.makedirs(save_dir, exist_ok=True)
            
            # 파일 저장
            file_path = os.path.join(save_dir, filename)
            
            # 바이트 데이터인 경우
            if isinstance(file_data, bytes):
                with open(file_path, 'wb') as f:
                    f.write(file_data)
            # 파일 객체인 경우
            else:
                file_data.seek(0)  # 파일 포인터를 처음으로 이동
                with open(file_path, 'wb') as f:
                    f.write(file_data.read())
            
            logger.info(f"파일 '{filename}' 로컬 저장 완료: {file_path}")
            
            # 로컬 경로 반환
            return f"local://{course_id}/{content_type}/{filename}"
            
        except Exception as e:
            logger.error(f"파일 '{filename}' 로컬 저장 중 오류 발생: {str(e)}")
            return ""
    
    async def get_file_url(self, storage_path: str) -> Optional[str]:
        """
        파일의 URL 생성
        
        Args:
            storage_path: 스토리지 경로
            
        Returns:
            Optional[str]: 파일 URL
        """
        if not storage_path:
            return None
            
        # 로컬 파일인 경우
        if storage_path.startswith("local://"):
            local_path = storage_path.replace("local://", "")
            full_path = os.path.join(self.local_download_dir, local_path)
            
            if os.path.exists(full_path):
                return f"file://{full_path}"
            else:
                logger.warning(f"로컬 파일을 찾을 수 없음: {full_path}")
                return None
                
        # Supabase Storage 파일인 경우
        try:
            if self.supabase:
                storage = self.supabase.storage.from_(self.bucket_name)
                signed_url = storage.create_signed_url(storage_path, 60 * 60)  # 1시간 유효
                return signed_url['signedURL']
        except Exception as e:
            logger.error(f"서명된 URL 생성 중 오류 발생: {str(e)}")
            
        return None
    
    async def delete_file(self, storage_path: str) -> bool:
        """
        파일 삭제
        
        Args:
            storage_path: 스토리지 경로
            
        Returns:
            bool: 삭제 성공 여부
        """
        if not storage_path:
            return False
            
        # 로컬 파일인 경우
        if storage_path.startswith("local://"):
            try:
                local_path = storage_path.replace("local://", "")
                full_path = os.path.join(self.local_download_dir, local_path)
                
                if os.path.exists(full_path):
                    os.remove(full_path)
                    logger.info(f"로컬 파일 삭제 완료: {full_path}")
                    return True
                else:
                    logger.warning(f"삭제할 로컬 파일을 찾을 수 없음: {full_path}")
                    return False
            except Exception as e:
                logger.error(f"로컬 파일 삭제 중 오류 발생: {str(e)}")
                return False
                
        # Supabase Storage 파일인 경우
        try:
            if self.supabase:
                storage = self.supabase.storage.from_(self.bucket_name)
                storage.remove(storage_path)
                logger.info(f"Supabase 파일 삭제 완료: {storage_path}")
                return True
        except Exception as e:
            logger.error(f"Supabase 파일 삭제 중 오류 발생: {str(e)}")
            
        return False
    
    async def get_attachments_by_source(self, source_type: str, source_id: int, user_id: str, db: AsyncSession) -> List[Attachment]:
        """
        특정 출처(공지사항, 강의자료, 과제 등)의 첨부파일 목록 조회
        
        Args:
            source_type: 출처 유형 ('notices', 'materials', 'assignments' 등)
            source_id: 출처 ID
            user_id: 사용자 ID (권한 확인용)
            db: 데이터베이스 세션
            
        Returns:
            List[Attachment]: 첨부파일 목록
        """
        try:
            logger.info(f"{source_type} ID {source_id}의 첨부파일 조회")
            
            # 첨부파일 쿼리
            stmt = select(Attachment).where(
                Attachment.source_type == source_type,
                Attachment.source_id == str(source_id)
            )
            result = await db.execute(stmt)
            attachments = list(result.scalars().all())

            if not attachments:
                logger.info(f"{source_type} ID {source_id}에 첨부파일이 없습니다.")
                return []
                
            # 각 첨부파일에 대한 접근 권한 확인
            # 이 경우 모든 첨부파일이 같은 강의에 속하므로 첫 번째 파일의 권한만 확인
            if attachments:
                # 첫 번째 첨부파일의 course_id 확인
                course_id = attachments[0].course_id
                
                # 접근 권한 확인 (실패 시 예외 발생)
                from app.core.security import verify_course_access
                await verify_course_access(user_id, course_id, db)
            
            # 첨부파일 URL 추가
            for attachment in attachments:
                if hasattr(attachment, 'storage_path') and attachment.storage_path:
                    # 임시 URL 필드 추가 (실제 DB 모델에는 없음)
                    attachment.download_url = await self.get_file_url(attachment.storage_path)
            
            logger.info(f"{len(attachments)}개의 첨부파일 반환")
            return attachments
            
        except Exception as e:
            logger.error(f"첨부파일 조회 중 오류 발생: {str(e)}")
            return []
    
    async def get_download_url(self, attachment_id: int, user_id: str, db: AsyncSession) -> Optional[str]:
        """
        첨부파일 다운로드 URL 생성 (권한 확인 포함)
        
        Args:
            attachment_id: 첨부파일 ID
            user_id: 사용자 ID (권한 확인용)
            db: 데이터베이스 세션
            
        Returns:
            Optional[str]: 다운로드 URL (권한이 없거나 파일을 찾을 수 없는 경우 None)
        """
        try:
            logger.info(f"첨부파일 ID {attachment_id}의 다운로드 URL 요청")
            
            # 첨부파일 접근 권한 확인 (실패 시 예외 발생)
            attachment = await verify_attachment_access(user_id, attachment_id, db)
            
            if not attachment.storage_path:
                logger.warning(f"첨부파일 ID {attachment_id}의 storage_path가 없습니다.")
                return None
                
            # 다운로드 URL 생성
            url = await self.get_file_url(attachment.storage_path)
            
            if not url:
                logger.warning(f"첨부파일 ID {attachment_id}의 URL을 생성할 수 없습니다.")
                return None
                
            logger.info(f"첨부파일 ID {attachment_id}의 다운로드 URL 생성 완료")
            return url
            
        except Exception as e:
            logger.error(f"다운로드 URL 생성 중 오류 발생: {str(e)}")
            return None

    async def get_attachment(self, attachment_id: int, user_id: str, db: AsyncSession) -> Optional[Dict[str, Any]]:
        """
        특정 첨부파일 메타데이터 조회 (권한 확인 포함)

        Args:
            attachment_id: 첨부파일 ID
            user_id: 사용자 ID (권한 확인용)
            db: 데이터베이스 세션

        Returns:
            Optional[Dict[str, Any]]: 첨부파일 정보
        """
        try:
            logger.info(f"첨부파일 ID {attachment_id} 조회")

            # 첨부파일 접근 권한 확인 (실패 시 예외 발생)
            attachment = await verify_attachment_access(user_id, attachment_id, db)

            # 딕셔너리로 변환
            result = attachment.to_dict() if hasattr(attachment, 'to_dict') else vars(attachment)

            # 다운로드 URL 추가
            if attachment.storage_path:
                result['download_url'] = await self.get_file_url(attachment.storage_path)

            logger.info(f"첨부파일 ID {attachment_id} 조회 완료")
            return result

        except Exception as e:
            logger.error(f"첨부파일 조회 중 오류 발생: {str(e)}")
            return None

    async def search_attachments(self, query: str, user_id: str, db: AsyncSession) -> List[Attachment]:
        """
        첨부파일 검색 (파일명, 소스 타입 등으로 검색)

        Args:
            query: 검색어
            user_id: 사용자 ID (권한 확인용)
            db: 데이터베이스 세션

        Returns:
            List[Attachment]: 검색 결과
        """
        try:
            logger.info(f"첨부파일 검색: {query}")

            # 사용자의 강의 목록 조회 (권한이 있는 강의만)
            from app.db.repositories.course_repository import CourseRepository
            course_repo = CourseRepository()
            user_courses = await course_repo.get_by_user_id(db, user_id)
            user_course_ids = [course.id for course in user_courses]

            if not user_course_ids:
                logger.warning(f"사용자 {user_id}의 강의가 없습니다.")
                return []

            # 첨부파일 검색
            search_term = f"%{query}%"  # 부분 일치 검색을 위한 와일드카드

            # 첨부파일 쿼리
            stmt = (
                select(Attachment)
                .where(
                    Attachment.course_id.in_(user_course_ids),  # 사용자의 강의에 속한 첨부파일만
                    sqlalchemy.or_(
                        Attachment.file_name.ilike(search_term),
                        Attachment.source_type.ilike(search_term)
                    )
                )
                .order_by(Attachment.created_at.desc())
            )

            result = await db.execute(stmt)
            attachments = list(result.scalars().all())

            # 첨부파일 URL 추가
            for attachment in attachments:
                if hasattr(attachment, 'storage_path') and attachment.storage_path:
                    # 임시 URL 필드 추가 (실제 DB 모델에는 없음)
                    attachment.download_url = await self.get_file_url(attachment.storage_path)

            logger.info(f"첨부파일 검색 결과: {len(attachments)}개")
            return attachments

        except Exception as e:
            logger.error(f"첨부파일 검색 중 오류 발생: {str(e)}")
            return []
