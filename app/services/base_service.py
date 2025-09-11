from abc import ABC, abstractmethod

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
