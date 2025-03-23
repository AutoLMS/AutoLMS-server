import logging
from typing import Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.base_service import BaseService
from app.services.session.eclass_session_manager import EclassSessionManager
from app.services.parsers.syllabus_parser import SyllabusParser
from app.db.repositories.syllabus_repository import SyllabusRepository

logger = logging.getLogger(__name__)

class SyllabusService(BaseService):
    """강의계획서 관련 서비스"""
    
    def __init__(
        self,
        eclass_session: EclassSessionManager,
        syllabus_parser: SyllabusParser,
        syllabus_repository: SyllabusRepository
    ):
        self.session_service = eclass_session
        self.parser = syllabus_parser
        self.repository = syllabus_repository
        logger.info("SyllabusService 초기화 완료")
    
    async def initialize(self) -> None:
        """서비스 초기화"""
        logger.info("SyllabusService 시작")
        pass
    
    async def close(self) -> None:
        """서비스 리소스 정리"""
        logger.info("SyllabusService 종료")
        pass
    
    async def get_syllabus(
        self, 
        user_id: str, 
        course_id: str, 
        db: AsyncSession, 
        force_refresh: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        강의계획서 조회
        
        Args:
            user_id: 사용자 ID
            course_id: 강의 ID
            db: 데이터베이스 세션
            force_refresh: 강제 새로고침 여부
            
        Returns:
            Optional[Dict[str, Any]]: 강의계획서 정보
        """
        logger.info(f"강의 {course_id}의 강의계획서 조회 시작 (user_id: {user_id})")
        
        # 이미 저장된 강의계획서 확인
        if not force_refresh:
            existing_syllabus = await self.repository.get_by_course_id(db, course_id)
            if existing_syllabus:
                logger.info(f"저장된 강의계획서 반환 (course_id: {course_id})")
                return existing_syllabus.to_dict() if hasattr(existing_syllabus, 'to_dict') else vars(existing_syllabus)
        
        # 새로운 강의계획서 조회
        try:
            # 이클래스 세션 가져오기
            eclass_session = await self.session_service.get_session(user_id)
            if not eclass_session:
                logger.error("이클래스 세션을 가져올 수 없음")
                return None
            
            # 강의계획서 URL 구성 및 요청
            base_url = "https://eclass.seoultech.ac.kr"
            syllabus_url = f"{base_url}/lecture/course_info.jsp?ref=1&ud={user_id}&ky={course_id}"
            
            response = await eclass_session.get(syllabus_url)
            if not response:
                logger.error(f"강의계획서 페이지 요청 실패 (course_id: {course_id})")
                return None
            
            # 강의계획서 파싱
            syllabus_data = self.parser.parse_syllabus(response.text)
            if not syllabus_data:
                logger.warning(f"강의계획서 파싱 결과 없음 (course_id: {course_id})")
                return None
            
            # JSON 형태로 변환
            syllabus_json = {
                'course_id': course_id,
                'content': syllabus_data
            }
            
            # 저장소에 저장
            existing_syllabus = await self.repository.get_by_course_id(db, course_id)
            if existing_syllabus:
                updated_syllabus = await self.repository.update(db, existing_syllabus.id, syllabus_json)
                saved_syllabus = updated_syllabus
            else:
                saved_syllabus = await self.repository.create(db, syllabus_json)
            
            logger.info(f"강의계획서 조회 완료 (course_id: {course_id})")
            return saved_syllabus.to_dict() if hasattr(saved_syllabus, 'to_dict') else vars(saved_syllabus)
            
        except Exception as e:
            logger.error(f"강의계획서 조회 중 오류 발생: {str(e)}")
            return None
    
    async def refresh_syllabus(self, user_id: str, course_id: str, db: AsyncSession) -> Dict[str, Any]:
        """
        강의계획서 새로고침
        
        Args:
            user_id: 사용자 ID
            course_id: 강의 ID
            db: 데이터베이스 세션
            
        Returns:
            Dict[str, Any]: 새로고침 결과
        """
        result = {"count": 0, "success": 0, "errors": 0}
        
        try:
            result["count"] = 1
            syllabus = await self.get_syllabus(user_id, course_id, db, force_refresh=True)
            
            if syllabus:
                result["success"] = 1
            else:
                result["errors"] = 1
                
        except Exception as e:
            logger.error(f"강의계획서 새로고침 중 오류 발생: {str(e)}")
            result["count"] = 1
            result["errors"] = 1
        
        return result
        
    async def refresh_all(self, db: AsyncSession, course_id: str, user_id: str) -> Dict[str, Any]:
        """
        강의계획서 새로고침 (다른 서비스와 형식 통일)
        
        Args:
            db: 데이터베이스 세션
            course_id: 강의 ID
            user_id: 사용자 ID
            
        Returns:
            Dict[str, Any]: 새로고침 결과
        """
        # refresh_syllabus 메서드를 호출하여 새로고침 작업 수행
        result = await self.refresh_syllabus(user_id, course_id, db)
        
        # 결과 형식 변환 (다른 서비스와 형식 통일)
        # 'count'/'success' 대신 'count'/'new' 사용
        return {
            "count": result.get("count", 0),
            "new": result.get("success", 0),
            "errors": result.get("errors", 0)
        }
