"""
eClass 비밀번호 암호화/복호화 서비스
"""
import base64
from cryptography.fernet import Fernet

class EncryptionService:
    """eClass 비밀번호 암호화/복호화 서비스"""
    
    def __init__(self):
        """암호화 키 초기화"""
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
    
    def _get_or_create_key(self) -> bytes:
        """암호화 키 생성 또는 가져오기"""
        from app.core.config import settings
        
        # 환경변수에서 키 가져오기 (없으면 생성)
        key_string = getattr(settings, 'ECLASS_ENCRYPTION_KEY', None)
        
        if key_string:
            try:
                return base64.urlsafe_b64decode(key_string.encode())
            except Exception:
                pass
        
        # 키가 없거나 잘못된 경우 새로 생성
        key = Fernet.generate_key()
        key_string = base64.urlsafe_b64encode(key).decode()
        
        print("🔑 새로운 암호화 키가 생성되었습니다.")
        print(f"환경변수에 다음을 추가하세요: ECLASS_ENCRYPTION_KEY={key_string}")
        
        return key
    
    def encrypt_password(self, password: str) -> str:
        """비밀번호 암호화"""
        try:
            if not password:
                return ""
            
            encrypted_bytes = self.cipher.encrypt(password.encode())
            return base64.urlsafe_b64encode(encrypted_bytes).decode()
        
        except Exception as e:
            print(f"❌ 비밀번호 암호화 실패: {e}")
            raise Exception("비밀번호 암호화 중 오류가 발생했습니다.")
    
    def decrypt_password(self, encrypted_password: str) -> str:
        """비밀번호 복호화"""
        try:
            if not encrypted_password:
                return ""
            
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_password.encode())
            decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
            return decrypted_bytes.decode()
        
        except Exception as e:
            print(f"❌ 비밀번호 복호화 실패: {e}")
            raise Exception("비밀번호 복호화 중 오류가 발생했습니다.")
    
    def is_encrypted(self, password: str) -> bool:
        """문자열이 암호화된 비밀번호인지 확인"""
        try:
            if not password:
                return False
            
            # Base64 디코딩과 Fernet 복호화 시도
            encrypted_bytes = base64.urlsafe_b64decode(password.encode())
            self.cipher.decrypt(encrypted_bytes)
            return True
        
        except Exception:
            return False


# 전역 인스턴스 (싱글톤 패턴)
_encryption_service = None

def get_encryption_service() -> EncryptionService:
    """암호화 서비스 인스턴스 반환"""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service