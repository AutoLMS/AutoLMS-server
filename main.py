import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys

from app.core.config import settings
from app.api.api import api_router

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

def create_app() -> FastAPI:
    """FastAPI 애플리케이션 생성"""
    app = FastAPI(
        title="AutoLMS",
        description="서울과학기술대학교 e-Class 자동화 시스템",
        version="1.0.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
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

app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.RELOAD)
