from typing import Generator

from app.db.base import SessionLocal

def get_db() -> Generator:
    """DB 세션 생성 및 관리"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
