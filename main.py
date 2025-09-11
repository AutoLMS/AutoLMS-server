import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys
import socket
from contextlib import closing, asynccontextmanager

logger = logging.getLogger(__name__)

from app.core.config import settings
from app.api.api import api_router
from app.services.scheduler_service import scheduler_service
from app.services.auto_refresh_service import auto_refresh_service

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)

# 각 모듈의 로거 레벨 설정
logging.getLogger('app.core.parsers.eclass_parser').setLevel(logging.DEBUG)
logging.getLogger('app.services').setLevel(logging.DEBUG)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 라이프사이클 관리"""
    # 시작 시
    logger.info("AutoLMS 애플리케이션 시작")
    
    try:
        # 자동 새로고침 서비스 초기화
        await auto_refresh_service.initialize()
        logger.info("자동 새로고침 서비스 초기화 완료")
        
        # 백그라운드 스케줄러 시작
        await scheduler_service.start()
        logger.info("백그라운드 스케줄러 시작 완료")
        
    except Exception as e:
        logger.error(f"서비스 초기화 중 오류: {str(e)}")
    
    yield  # 애플리케이션 실행
    
    # 종료 시
    logger.info("AutoLMS 애플리케이션 종료 시작")
    
    try:
        # 백그라운드 스케줄러 정지
        await scheduler_service.stop()
        logger.info("백그라운드 스케줄러 정지 완료")
        
        # 기타 리소스 정리
        logger.info("리소스 정리 완료")
        
    except Exception as e:
        logger.error(f"서비스 종료 중 오류: {str(e)}")
    
    logger.info("AutoLMS 애플리케이션 종료 완료")

def create_app() -> FastAPI:
    """FastAPI 애플리케이션 생성"""
    app = FastAPI(
        title="AutoLMS",
        description="서울과학기술대학교 e-Class 자동화 시스템",
        version="1.0.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan  # 라이프사이클 관리 추가
    )

    # CORS 설정
    origins = settings.get_cors_origins()
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # API 라우터 포함
    app.include_router(api_router, prefix=settings.API_V1_STR)

    @app.get("/")
    def root():
        return {"message": f"Welcome to {settings.API_V1_STR}"}

    return app

def is_port_in_use(host: str, port: int) -> bool:
    """포트가 이미 사용 중인지 확인"""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        return s.connect_ex((host, port)) == 0

def find_available_port(host: str, start_port: int, max_attempts: int = 10) -> int:
    """사용 가능한 포트 찾기"""
    port = start_port
    for _ in range(max_attempts):
        if not is_port_in_use(host, port):
            return port
        port += 1
    # 모든 시도 후에도 사용 가능한 포트를 찾지 못한 경우
    raise RuntimeError(f"{max_attempts}번의 시도 후에도 사용 가능한 포트를 찾지 못했습니다.")

app = create_app()

if __name__ == "__main__":
    # 설정된 포트가 이미 사용 중인지 확인
    host = settings.HOST
    port = settings.PORT

    if is_port_in_use(host, port):
        logger.warning(f"포트 {port}가 이미 사용 중입니다. 다른 포트를 찾습니다.")
        port = find_available_port(host, port + 1)
        logger.info(f"사용 가능한 포트를 찾았습니다: {port}")

    logger.info(f"서버를 시작합니다: {host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=settings.RELOAD)
