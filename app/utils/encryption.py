"""
이클래스 비밀번호 암호화/복호화 유틸리티

AES-256 암호화를 사용하여 이클래스 비밀번호를 안전하게 저장합니다.
환경변수 ECLASS_ENCRYPTION_KEY를 암호화 키로 사용합니다.
"""

import logging
import base64
import hashlib
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings

logger = logging.getLogger(__name__)


class EncryptionError(Exception):
    """암호화 관련 예외"""
    pass


class DecryptionError(Exception):
    """복호화 관련 예외"""
    pass


def _get_fernet_key() -> bytes:
    """환경변수에서 Fernet 키 생성"""
    if not settings.ECLASS_ENCRYPTION_KEY:
        raise EncryptionError("ECLASS_ENCRYPTION_KEY가 설정되지 않았습니다")
    
    try:
        # Base64 디코딩 시도 (직접 생성된 키인 경우)
        key_bytes = base64.urlsafe_b64decode(settings.ECLASS_ENCRYPTION_KEY.encode())
        if len(key_bytes) == 32:  # 32바이트 키인 경우
            return base64.urlsafe_b64encode(key_bytes)
        else:
            raise ValueError("Invalid key length")
    except Exception:
        # 일반 문자열인 경우 PBKDF2로 키 파생
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'autolms_eclass_salt',  # 고정 솔트 (실제 운영 시 변경 권장)
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(settings.ECLASS_ENCRYPTION_KEY.encode()))
        return key


def encrypt_eclass_password(password: str) -> str:
    """
    이클래스 비밀번호를 AES-256으로 암호화
    
    Args:
        password: 평문 이클래스 비밀번호
        
    Returns:
        str: Base64 인코딩된 암호화된 비밀번호
        
    Raises:
        EncryptionError: 암호화 실패 시
    """
    if not password:
        raise EncryptionError("암호화할 비밀번호가 비어있습니다")
    
    try:
        key = _get_fernet_key()
        fernet = Fernet(key)
        encrypted_bytes = fernet.encrypt(password.encode('utf-8'))
        encrypted_password = base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
        
        logger.debug("이클래스 비밀번호 암호화 완료")
        return encrypted_password
        
    except Exception as e:
        logger.error(f"이클래스 비밀번호 암호화 실패: {str(e)}")
        raise EncryptionError(f"비밀번호 암호화에 실패했습니다: {str(e)}")


def decrypt_eclass_password(encrypted_password: str) -> str:
    """
    암호화된 이클래스 비밀번호를 복호화
    
    Args:
        encrypted_password: Base64 인코딩된 암호화된 비밀번호
        
    Returns:
        str: 복호화된 평문 비밀번호
        
    Raises:
        DecryptionError: 복호화 실패 시
    """
    if not encrypted_password:
        raise DecryptionError("복호화할 암호화된 비밀번호가 비어있습니다")
    
    try:
        key = _get_fernet_key()
        fernet = Fernet(key)
        
        # Base64 디코딩
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_password.encode('utf-8'))
        
        # 복호화
        decrypted_bytes = fernet.decrypt(encrypted_bytes)
        password = decrypted_bytes.decode('utf-8')
        
        logger.debug("이클래스 비밀번호 복호화 완료")
        return password
        
    except InvalidToken:
        logger.error("잘못된 암호화 토큰으로 인한 복호화 실패")
        raise DecryptionError("잘못된 암호화 데이터입니다")
    except Exception as e:
        logger.error(f"이클래스 비밀번호 복호화 실패: {str(e)}")
        raise DecryptionError(f"비밀번호 복호화에 실패했습니다: {str(e)}")


def is_encrypted(password: str) -> bool:
    """
    비밀번호가 암호화되어 있는지 확인
    
    Args:
        password: 확인할 비밀번호 문자열
        
    Returns:
        bool: 암호화된 경우 True, 평문인 경우 False
    """
    if not password:
        return False
        
    try:
        # Base64 디코딩 가능한지 확인
        base64.urlsafe_b64decode(password.encode('utf-8'))
        
        # Fernet 토큰 형식인지 확인 (실제 복호화 시도)
        decrypt_eclass_password(password)
        return True
        
    except Exception:
        return False


def validate_encryption_setup() -> bool:
    """
    암호화 설정이 올바른지 검증
    
    Returns:
        bool: 설정이 올바른 경우 True
    """
    try:
        # 테스트 암호화/복호화
        test_password = "test_password_123"
        encrypted = encrypt_eclass_password(test_password)
        decrypted = decrypt_eclass_password(encrypted)
        
        return decrypted == test_password
        
    except Exception as e:
        logger.error(f"암호화 설정 검증 실패: {str(e)}")
        return False


# 모듈 초기화 시 암호화 설정 검증
try:
    if not validate_encryption_setup():
        logger.warning("암호화 설정 검증에 실패했습니다. ECLASS_ENCRYPTION_KEY를 확인해주세요.")
except Exception as e:
    logger.error(f"암호화 모듈 초기화 실패: {str(e)}")