import logging
from typing import List, Dict, Any, Optional, Type, Generic, TypeVar
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.base_service import BaseService, ContentService as ContentServiceBase
from app.services.session_service import SessionService
from app.services.parsers.content_parser import ContentParser
from app.db.repositories.base import BaseRepository
from app.db.base import Base

logger = logging.getLogger(__name__)

ModelType = TypeVar('ModelType', bound=Base)
RepositoryType = TypeVar('RepositoryType', bound=BaseRepository)
ParserType = TypeVar('ParserType', bound=ContentParser)

class ContentService(ContentServiceBase, Generic[ModelType, ParserType, RepositoryType]):
    """콘텐츠 서비스 구현 클래스"""
    
    def __init__(
        self,
        session_service: SessionService,
        parser: ParserType,
        repository: RepositoryType,
        content_type: str
    ):
        self.session_service = session_service
        self.parser = parser
        self.repository = repository
        self.content_type = content_type  # 'notices', 'materials', 'assignments' 등
        logger.info(f"{self.content_type.capitalize()}Service 초기화 완료")
    
    async def initialize(self) -> None:
        """서비스 초기화"""
        logger.info(f"{self.content_type.capitalize()}Service 시작")
        pass
    
    async def close(self) -> None:
        """서비스 리소스 정리"""
        logger.info(f"{self.content_type.capitalize()}Service 종료")
        pass
    
    async def get_by_id(self, db: AsyncSession, id: str) -> Optional[ModelType]:
        """ID로 항목 조회"""
        return await self.repository.get_by_id(db, id)
    
    async def get_all(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """모든 항목 조회"""
        return await self.repository.get_all(db, skip=skip, limit=limit)
    
    async def get_by_course_id(self, db: AsyncSession, course_id: str, user_id: str = None) -> List[ModelType]:
        """강의 ID로 항목 조회"""
        return await self.repository.get_by_course_id(db, course_id)
    
    async def create(self, db: AsyncSession, obj_in: Dict[str, Any]) -> ModelType:
        """항목 생성"""
        return await self.repository.create(db, obj_in)
    
    async def update(self, db: AsyncSession, id: str, obj_in: Dict[str, Any]) -> Optional[ModelType]:
        """항목 업데이트"""
        return await self.repository.update(db, id, obj_in)
    
    async def delete(self, db: AsyncSession, id: str) -> bool:
        """항목 삭제"""
        return await self.repository.delete(db, id)
    
    async def refresh_all(self, db: AsyncSession, course_id: str, user_id: str, auto_download: bool = False) -> Dict[str, Any]:
        """
        콘텐츠 새로고침 - 구체적인 구현은 하위 클래스에서 담당
        """
        raise NotImplementedError("하위 클래스에서 구현해야 합니다")
