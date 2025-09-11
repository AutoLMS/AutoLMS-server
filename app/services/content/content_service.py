import logging
from typing import List, Dict, Any, Optional, Generic, TypeVar

from app.services.base_service import BaseService
from app.services.session import EclassSessionManager
from app.services.parsers.content_parser import ContentParser

logger = logging.getLogger(__name__)

RepositoryType = TypeVar('RepositoryType')
ParserType = TypeVar('ParserType', bound=ContentParser)

class ContentService(BaseService, Generic[ParserType, RepositoryType]):
    """콘텐츠 서비스 구현 클래스"""
    
    def __init__(
        self,
        session_service: EclassSessionManager,
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
    
    async def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """ID로 항목 조회"""
        return await self.repository.get_by_id(id)
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """모든 항목 조회"""
        return await self.repository.get_all(skip=skip, limit=limit)
    
    async def get_by_course_id(self, course_id: str, user_id: str = None) -> List[Dict[str, Any]]:
        """강의 ID로 항목 조회"""
        return await self.repository.get_by_course_id(course_id)
    
    async def create(self, obj_in: Dict[str, Any]) -> Dict[str, Any]:
        """항목 생성"""
        return await self.repository.create(obj_in)
    
    async def update(self, id: str, obj_in: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """항목 업데이트"""
        return await self.repository.update(id, obj_in)
    
    async def delete(self, id: str) -> bool:
        """항목 삭제"""
        return await self.repository.delete(id)
    
    async def refresh_all(self, course_id: str, user_id: str, auto_download: bool = False) -> Dict[str, Any]:
        """
        콘텐츠 새로고침 - 구체적인 구현은 하위 클래스에서 담당
        """
        raise NotImplementedError("하위 클래스에서 구현해야 합니다")

