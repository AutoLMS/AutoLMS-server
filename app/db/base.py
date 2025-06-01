from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# 기본 Base 클래스 생성
Base = declarative_base()

# 엔진 생성
engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI, 
    pool_pre_ping=True, 
    echo=False,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=30,
    pool_recycle=3600
)

# 세션 팩토리 생성
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 모든 모델 클래스 임포트
# 이렇게 하면 Base 클래스의 metadata에 모든 모델이 등록됨
from app.models.course import Course
from app.models.notice import Notice
from app.models.material import Material
from app.models.assignment import Assignment
from app.models.attachment import Attachment
from app.models.syllabus import Syllabus

# 모든 모델이 Base를 상속받아야 함
# 각 모델 파일에서 다음과 같이 정의되어 있어야 함:
# class ModelName(Base):
#     __tablename__ = "table_name"
#     ...
