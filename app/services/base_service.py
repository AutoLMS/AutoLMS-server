from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, TypeVar, Generic
from sqlalchemy.ext.asyncio import AsyncSession

# 타입 변수 정의
ModelType = TypeVar('ModelType')
CreateSchemaType = TypeVar('CreateSchemaType')
UpdateSchemaType = TypeVar('UpdateSchemaType')

class BaseService(ABC):
    """
    모든 서비스의 기본 인터페이스.
    서비스 계층의 공통 메서드를 정의합니다.
    """
    
    @abstractmethod
    async def initialize(self) -> None:
        """서비스 초기화"""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """서비스 리소스 정리"""
        pass


class ContentService(BaseService, Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    콘텐츠 관련 서비스를 위한 추상 기본 클래스.
    공지사항, 강의자료, 과제 등 콘텐츠 관련 서비스의 공통 인터페이스를 정의합니다.
    """
    
    @abstractmethod
    async def get_by_id(self, db: AsyncSession, id: str) -> Optional[ModelType]:
        """ID로 항목 조회"""
        pass
    
    @abstractmethod
    async def get_all(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """모든 항목 조회"""
        pass
    
    @abstractmethod
    async def get_by_course_id(self, db: AsyncSession, course_id: str, user_id: str = None) -> List[ModelType]:
        """강의 ID로 항목 조회"""
        pass
    
    @abstractmethod
    async def create(self, db: AsyncSession, obj_in: CreateSchemaType) -> ModelType:
        """항목 생성"""
        pass
    
    @abstractmethod
    async def update(self, db: AsyncSession, id: str, obj_in: UpdateSchemaType) -> Optional[ModelType]:
        """항목 업데이트"""
        pass
    
    @abstractmethod
    async def delete(self, db: AsyncSession, id: str) -> bool:
        """항목 삭제"""
        pass
    
    @abstractmethod
    async def refresh_all(self, db: AsyncSession, course_id: str, user_id: str, auto_download: bool = False) -> Dict[str, Any]:
        """
        특정 강의의 모든 항목 새로고침
        
        Args:
            db: 데이터베이스 세션
            course_id: 강의 ID
            user_id: 사용자 ID
            auto_download: 첨부파일 자동 다운로드 여부
            
        Returns:
            Dict[str, Any]: 새로고침 결과 (count, new, errors 등)
        """
        pass
