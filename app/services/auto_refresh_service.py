import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from app.core.supabase_client import get_supabase_client
from app.services.session.eclass_session_manager import EclassSessionManager
from app.services.content import NoticeService, MaterialService, AssignmentService

logger = logging.getLogger(__name__)

@dataclass
class AutoRefreshConfig:
    """자동 새로고침 설정"""
    user_id: str
    course_id: str
    enabled: bool = True
    refresh_notices: bool = True
    refresh_materials: bool = True
    refresh_assignments: bool = True
    last_refresh: Optional[datetime] = None
    refresh_interval_hours: int = 2  # 기본 2시간마다

class AutoRefreshService:
    """자동 콘텐츠 새로고침 서비스"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        self.eclass_session_manager = EclassSessionManager()
        self.refresh_configs: Dict[str, AutoRefreshConfig] = {}
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """서비스 초기화"""
        logger.info("AutoRefreshService 초기화 시작")
        await self._load_refresh_configs()
        logger.info("AutoRefreshService 초기화 완료")
    
    async def _load_refresh_configs(self) -> None:
        """데이터베이스에서 자동 새로고침 설정 로드"""
        try:
            # user_courses 테이블에서 활성 사용자-강의 조합 조회
            result = self.supabase.table('user_courses')\
                .select('user_id, course_id, created_at')\
                .execute()
            
            if result.data:
                for row in result.data:
                    config_key = f"{row['user_id']}:{row['course_id']}"
                    self.refresh_configs[config_key] = AutoRefreshConfig(
                        user_id=row['user_id'],
                        course_id=row['course_id']
                    )
                
                logger.info(f"자동 새로고침 설정 {len(result.data)}개 로드 완료")
            
        except Exception as e:
            logger.error(f"자동 새로고침 설정 로드 중 오류: {str(e)}")
    
    async def add_auto_refresh_config(self, user_id: str, course_id: str, **kwargs) -> None:
        """자동 새로고침 설정 추가"""
        config_key = f"{user_id}:{course_id}"
        
        async with self._lock:
            self.refresh_configs[config_key] = AutoRefreshConfig(
                user_id=user_id,
                course_id=course_id,
                **kwargs
            )
        
        logger.info(f"자동 새로고침 설정 추가: {config_key}")
    
    async def remove_auto_refresh_config(self, user_id: str, course_id: str) -> None:
        """자동 새로고침 설정 제거"""
        config_key = f"{user_id}:{course_id}"
        
        async with self._lock:
            if config_key in self.refresh_configs:
                del self.refresh_configs[config_key]
                logger.info(f"자동 새로고침 설정 제거: {config_key}")
    
    async def refresh_user_content(self, user_id: str, force: bool = False) -> Dict[str, Any]:
        """특정 사용자의 모든 콘텐츠 새로고침"""
        results = {
            "user_id": user_id,
            "refreshed_courses": [],
            "errors": [],
            "total_new_items": 0
        }
        
        try:
            # 사용자의 모든 강의 설정 조회
            user_configs = [
                config for config in self.refresh_configs.values()
                if config.user_id == user_id
            ]
            
            if not user_configs:
                logger.info(f"사용자 {user_id}의 자동 새로고침 설정이 없습니다.")
                return results
            
            # 각 강의별로 새로고침 실행
            for config in user_configs:
                try:
                    # 새로고침 주기 체크 (force가 False인 경우)
                    if not force and not self._should_refresh(config):
                        continue
                    
                    course_result = await self._refresh_course_content(config)
                    results["refreshed_courses"].append(course_result)
                    results["total_new_items"] += course_result.get("total_new", 0)
                    
                    # 마지막 새로고침 시간 업데이트
                    config.last_refresh = datetime.now()
                    
                except Exception as course_error:
                    error_msg = f"강의 {config.course_id} 새로고침 중 오류: {str(course_error)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
            
            logger.info(f"사용자 {user_id} 콘텐츠 새로고침 완료: {results['total_new_items']}개 신규 항목")
            return results
            
        except Exception as e:
            error_msg = f"사용자 {user_id} 콘텐츠 새로고침 중 전체 오류: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            return results
    
    async def _refresh_course_content(self, config: AutoRefreshConfig) -> Dict[str, Any]:
        """특정 강의의 콘텐츠 새로고침"""
        result = {
            "course_id": config.course_id,
            "user_id": config.user_id,
            "notices": {"count": 0, "new": 0, "errors": 0},
            "materials": {"count": 0, "new": 0, "errors": 0},
            "assignments": {"count": 0, "new": 0, "errors": 0},
            "total_new": 0
        }
        
        try:
            # 이클래스 세션 확인
            eclass_session = await self.eclass_session_manager.get_session(config.user_id)
            if not eclass_session:
                raise Exception("이클래스 세션을 가져올 수 없습니다.")
            
            # 공지사항 새로고침
            if config.refresh_notices:
                try:
                    from app.api.deps import get_notice_service
                    notice_service = get_notice_service()
                    
                    notice_result = await notice_service.refresh_all(
                        course_id=config.course_id,
                        user_id=config.user_id,
                        auto_download=True
                    )
                    
                    result["notices"] = notice_result
                    result["total_new"] += notice_result.get("new", 0)
                    
                except Exception as e:
                    logger.error(f"공지사항 새로고침 중 오류: {str(e)}")
                    result["notices"]["errors"] = 1
            
            # 강의자료 새로고침
            if config.refresh_materials:
                try:
                    from app.api.deps import get_material_service
                    material_service = get_material_service()
                    
                    material_result = await material_service.refresh_all(
                        course_id=config.course_id,
                        user_id=config.user_id,
                        auto_download=True
                    )
                    
                    result["materials"] = material_result
                    result["total_new"] += material_result.get("new", 0)
                    
                except Exception as e:
                    logger.error(f"강의자료 새로고침 중 오류: {str(e)}")
                    result["materials"]["errors"] = 1
            
            # 과제 새로고침
            if config.refresh_assignments:
                try:
                    from app.api.deps import get_assignment_service
                    assignment_service = get_assignment_service()
                    
                    assignment_result = await assignment_service.refresh_all(
                        course_id=config.course_id,
                        user_id=config.user_id,
                        auto_download=True
                    )
                    
                    result["assignments"] = assignment_result
                    result["total_new"] += assignment_result.get("new", 0)
                    
                except Exception as e:
                    logger.error(f"과제 새로고침 중 오류: {str(e)}")
                    result["assignments"]["errors"] = 1
            
            logger.info(f"강의 {config.course_id} 새로고침 완료: {result['total_new']}개 신규 항목")
            return result
            
        except Exception as e:
            logger.error(f"강의 {config.course_id} 새로고침 중 오류: {str(e)}")
            raise
    
    def _should_refresh(self, config: AutoRefreshConfig) -> bool:
        """새로고침이 필요한지 판단"""
        if not config.enabled:
            return False
        
        if config.last_refresh is None:
            return True
        
        # 설정된 간격 이후에만 새로고침
        time_since_last = datetime.now() - config.last_refresh
        required_interval = timedelta(hours=config.refresh_interval_hours)
        
        return time_since_last >= required_interval
    
    async def refresh_all_active_users(self) -> Dict[str, Any]:
        """모든 활성 사용자의 콘텐츠 새로고침"""
        summary = {
            "total_users": 0,
            "refreshed_users": 0,
            "total_new_items": 0,
            "errors": []
        }
        
        try:
            # 최근 활성 사용자 조회 (24시간 이내)
            cutoff_time = (datetime.now() - timedelta(hours=24)).isoformat()
            
            result = self.supabase.table('sessions')\
                .select('user_id')\
                .gt('last_used', cutoff_time)\
                .eq('is_active', True)\
                .execute()
            
            if not result.data:
                logger.info("활성 사용자가 없습니다.")
                return summary
            
            # 중복 제거
            active_user_ids = list(set([row['user_id'] for row in result.data]))
            summary["total_users"] = len(active_user_ids)
            
            logger.info(f"활성 사용자 {len(active_user_ids)}명의 콘텐츠 자동 새로고침 시작")
            
            # 각 사용자별 새로고침
            for user_id in active_user_ids:
                try:
                    user_result = await self.refresh_user_content(user_id)
                    
                    if user_result["refreshed_courses"]:
                        summary["refreshed_users"] += 1
                        summary["total_new_items"] += user_result["total_new_items"]
                    
                    if user_result["errors"]:
                        summary["errors"].extend(user_result["errors"])
                    
                    # 사용자간 간격 두기 (서버 부하 방지)
                    await asyncio.sleep(2)
                    
                except Exception as user_error:
                    error_msg = f"사용자 {user_id} 처리 중 오류: {str(user_error)}"
                    logger.error(error_msg)
                    summary["errors"].append(error_msg)
            
            logger.info(f"전체 자동 새로고침 완료: {summary['refreshed_users']}/{summary['total_users']} 사용자, "
                       f"{summary['total_new_items']}개 신규 항목")
            
            return summary
            
        except Exception as e:
            error_msg = f"전체 자동 새로고침 중 오류: {str(e)}"
            logger.error(error_msg)
            summary["errors"].append(error_msg)
            return summary
    
    async def get_refresh_status(self, user_id: str) -> Dict[str, Any]:
        """사용자의 자동 새로고침 상태 조회"""
        status = {
            "user_id": user_id,
            "total_configs": 0,
            "enabled_configs": 0,
            "courses": []
        }
        
        user_configs = [
            config for config in self.refresh_configs.values()
            if config.user_id == user_id
        ]
        
        status["total_configs"] = len(user_configs)
        
        for config in user_configs:
            course_status = {
                "course_id": config.course_id,
                "enabled": config.enabled,
                "refresh_notices": config.refresh_notices,
                "refresh_materials": config.refresh_materials,
                "refresh_assignments": config.refresh_assignments,
                "last_refresh": config.last_refresh.isoformat() if config.last_refresh else None,
                "refresh_interval_hours": config.refresh_interval_hours,
                "should_refresh": self._should_refresh(config)
            }
            
            if config.enabled:
                status["enabled_configs"] += 1
            
            status["courses"].append(course_status)
        
        return status
    
    async def update_config(self, user_id: str, course_id: str, **updates) -> bool:
        """자동 새로고침 설정 업데이트"""
        config_key = f"{user_id}:{course_id}"
        
        async with self._lock:
            if config_key in self.refresh_configs:
                config = self.refresh_configs[config_key]
                
                # 허용된 필드만 업데이트
                allowed_fields = ['enabled', 'refresh_notices', 'refresh_materials', 
                                'refresh_assignments', 'refresh_interval_hours']
                
                for field, value in updates.items():
                    if field in allowed_fields and hasattr(config, field):
                        setattr(config, field, value)
                
                logger.info(f"자동 새로고침 설정 업데이트: {config_key}")
                return True
        
        return False

# 싱글톤 인스턴스
auto_refresh_service = AutoRefreshService()