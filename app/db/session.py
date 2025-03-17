from typing import Generator

from app.db.base import AsyncSessionLocal

def get_db() -> Generator:
    """DB 세션 생성 및 관리"""
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        db.close()
