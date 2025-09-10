# Auth System Refactor - API Changes

## 📅 Change Date: 2025-09-09

## 🗑️ Removed Components

### PostgreSQL User Model
- **File**: `app/models/user.py`
- **Status**: ❌ REMOVED
- **Reason**: Migrating to Supabase-only architecture

#### Model Definition (Before)
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    eclass_username = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    courses = relationship("Course", secondary="user_courses", back_populates="users")
    sessions = relationship("Session", back_populates="user")
```

### PostgreSQL User Repository
- **File**: `app/db/repositories/user_repository.py` 
- **Status**: ❌ REMOVED
- **Reason**: All user operations moved to Supabase

#### Repository Methods (Before)
- `get_by_id()`
- `get_by_email()` 
- `create()`
- `update()`
- `get_all()`
- `delete()`
- `get_or_create()`

## 🔄 Modified Components

### Course Model Relationships
- **File**: `app/models/course.py`
- **Change**: Removed User relationship
- **Impact**: ⚠️ **BREAKING CHANGE**

#### Before
```python
users = relationship("User", secondary=user_courses, back_populates="courses")
```

#### After
```python
# 관계 정의 - User 모델 제거로 인해 주석 처리
```

### Auth Service User Lookup
- **File**: `app/services/auth_service.py`  
- **Change**: `get_user_eclass_credentials()` method updated

#### Before (PostgreSQL)
```python
query = select(User).where(User.id == user_id)
result = await db.execute(query)
user = result.scalar_one_or_none()
```

#### After (Supabase)
```python
user_response = self.supabase.table('users').select('eclass_username, eclass_password').eq('id', user_id).execute()
```

### Model Package Exports
- **File**: `app/models/__init__.py`
- **Change**: Removed User from exports

#### Before
```python
from app.models.user import User
__all__ = ['User', 'Course', ...]
```

#### After
```python
__all__ = ['Course', 'Notice', ...]  # User removed
```

## 📊 Impact Assessment

### High Impact Changes
- ⚠️ **User-Course relationships broken** - Requires migration to Supabase user_courses
- ⚠️ **Session model relationships** - May need updating
- ⚠️ **Any direct User model imports** - Will cause ImportError

### Migration Required
- [ ] Existing PostgreSQL user data → Supabase users table
- [ ] Update any remaining User model references
- [ ] Test user_courses relationship functionality

## 🔄 Updated Components (Phase 2)

### Auth Service Refactor & JWT Integration
- **File**: `app/services/auth_service.py`
- **Date**: 2025-09-09
- **Status**: ✅ COMPLETED

#### Register Method Changes

**Before:**
```python
# UUID 랜덤 비밀번호
auto_password = str(uuid.uuid4())

# 평문 비밀번호 저장
user_data = {
    'eclass_password': eclass_password  # ❌ 평문 저장
}

# 사용자 정보만 반환
return {"user": {"id": user_id, "eclass_username": eclass_username}}
```

**After:**
```python
# eclass_username을 Supabase 비밀번호로 사용
auto_password = eclass_username

# 암호화된 비밀번호 저장
encrypted_eclass_password = encrypt_eclass_password(eclass_password)
user_data = {
    'eclass_password': encrypted_eclass_password  # ✅ AES-256 암호화
}

# Supabase JWT 토큰 포함하여 반환
return {
    "access_token": auth_response.session.access_token,
    "refresh_token": auth_response.session.refresh_token,
    "user": {"id": user_id, "eclass_username": eclass_username}
}
```

#### Login Method Changes

**Before:**
```python
# Supabase 테이블 직접 조회
user_response = self.supabase.table('users').select('*').eq('eclass_username', eclass_username)

# UUID 임시 토큰 생성
access_token = str(uuid.uuid4())

return {
    "session": {
        "access_token": access_token,    # ❌ UUID 토큰
        "refresh_token": str(uuid.uuid4())
    }
}
```

**After:**
```python
# Supabase Auth 로그인
auth_response = self.supabase.auth.sign_in_with_password({
    "email": f"seoultech@{eclass_username}",
    "password": eclass_username
})

# 이클래스 비밀번호 암호화 업데이트
await self._update_eclass_password(user_id, eclass_password)

return {
    "access_token": auth_response.session.access_token,   # ✅ Supabase JWT
    "refresh_token": auth_response.session.refresh_token
}
```

#### Password Management Methods

**New Methods Added:**
```python
async def _update_eclass_password(self, user_id: str, eclass_password: str):
    """이클래스 비밀번호를 암호화하여 업데이트"""
    # 기존 암호화된 비밀번호와 비교
    # 필요한 경우에만 재암호화하여 저장

async def get_user_eclass_credentials(self, user_id: str):
    """암호화된 비밀번호를 복호화하여 반환"""
    # 평문/암호화 상태 자동 감지
    # 기존 평문 데이터 호환성 지원
```

## 🔐 Security Improvements Applied

### Encryption Integration
- **AES-256 암호화**: 모든 이클래스 비밀번호는 저장 시 암호화
- **Backward Compatibility**: 기존 평문 비밀번호 자동 감지 및 처리
- **Safe Updates**: 로그인 시 점진적으로 평문 → 암호화 마이그레이션

### JWT Token Security
- **Standard Compliance**: Supabase JWT 표준 사용
- **Token Validation**: 내장된 만료 시간 및 서명 검증
- **Session Management**: Supabase Auth의 세션 관리 활용

## 📊 API Response Changes

### Register Endpoint Response
```json
// Before
{
  "user": {
    "id": "uuid",
    "eclass_username": "20241234"
  }
}

// After  
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "refresh_token_here",
  "user": {
    "id": "uuid", 
    "eclass_username": "20241234"
  }
}
```

### Login Endpoint Response
```json
// Before
{
  "session": {
    "access_token": "550e8400-e29b-41d4-a716-446655440000",  // UUID
    "refresh_token": "another-uuid-here"
  },
  "user": {...}
}

// After
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",  // Supabase JWT
  "refresh_token": "supabase_refresh_token_here",
  "user": {...}
}
```

## 🔗 Related Changes
- ✅ Implemented AES-256 encryption utilities
- ✅ Refactored auth service to use Supabase JWT tokens  
- 🔄 Next: Update session management to remove PostgreSQL dependencies
- 📋 Next: Implement course material access control with RLS