"""
eClass 비밀번호 암호화/복호화 서비스

비밀번호 변경 시나리오를 고려한 안전한 암호화 구현
"""
import base64
import os
from typing import Optional
from cryptography.fernet import Fernet
from app.core.config import settings


class EncryptionService:
    """eClass 비밀번호 암호화/복호화 서비스"""
    
    def __init__(self):
        self.cipher = self._get_cipher()
    
    def _get_cipher(self) -> Fernet:
        """암호화 키로 Fernet 객체 생성"""
        try:
            # 환경변수에서 키 가져오기 (없으면 자동 생성)
            encryption_key = getattr(settings, 'ECLASS_ENCRYPTION_KEY', None)
            
            if not encryption_key:
                # 키가 없으면 새로 생성
                key = Fernet.generate_key()
                encryption_key = base64.urlsafe_b64encode(key).decode()
                print(f"🔐 새 암호화 키 생성됨: {encryption_key}")
                print("📝 .env 파일에 다음 키를 추가해주세요:")
                print(f"ECLASS_ENCRYPTION_KEY={encryption_key}")
            
            # Base64 디코딩
            key_bytes = base64.urlsafe_b64decode(encryption_key.encode())
            return Fernet(key_bytes)
            
        except Exception as e:
            print(f"❌ 암호화 키 설정 실패: {e}")
            # 임시 키 생성 (개발 환경용)
            key = Fernet.generate_key()
            return Fernet(key)
    
    def encrypt_password(self, password: str) -> str:
        """비밀번호 암호화"""
        try:
            if not password:
                return ""
            
            # 문자열을 바이트로 변환 후 암호화
            encrypted_bytes = self.cipher.encrypt(password.encode())
            
            # Base64로 인코딩하여 문자열로 반환
            return base64.urlsafe_b64encode(encrypted_bytes).decode()
            
        except Exception as e:
            print(f"❌ 비밀번호 암호화 실패: {e}")
            raise Exception("비밀번호 암호화 중 오류가 발생했습니다.")
    
    def decrypt_password(self, encrypted_password: str) -> str:
        """암호화된 비밀번호 복호화"""
        try:
            if not encrypted_password:
                return ""
            
            # Base64 디코딩
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_password.encode())
            
            # 복호화 후 문자열로 변환
            decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
            return decrypted_bytes.decode()
            
        except Exception as e:
            print(f"❌ 비밀번호 복호화 실패: {e}")
            raise Exception("비밀번호 복호화 중 오류가 발생했습니다.")
    
    def is_encrypted(self, password: str) -> bool:
        """비밀번호가 암호화되어 있는지 확인"""
        try:
            if not password or len(password) < 20:
                return False
            
            # Base64 디코딩 시도
            base64.urlsafe_b64decode(password.encode())
            
            # 복호화 시도 (성공하면 암호화된 것)
            self.decrypt_password(password)
            return True
            
        except:
            # 디코딩/복호화 실패 시 평문으로 판단
            return False


# 싱글톤 인스턴스
_encryption_service = None

def get_encryption_service() -> EncryptionService:
    """암호화 서비스 싱글톤 인스턴스 반환"""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service