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

## 🔗 Related Changes
- Next: Implement encryption utilities for secure password storage
- Next: Refactor auth service to use Supabase JWT tokens
- Future: Update session management to remove PostgreSQL dependencies