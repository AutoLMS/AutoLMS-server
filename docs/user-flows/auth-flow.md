# User Authentication Flow - AutoLMS

## 📊 Complete Authentication Flow Diagram

```mermaid
flowchart TD
    A[사용자: 이클래스 ID/PW 입력] --> B{신규 사용자?}
    
    B -->|Yes| C[AuthService.register()]
    B -->|No| D[AuthService.login()]
    
    C --> C1[1. 이클래스 계정 검증<br/>EclassSession.login()]
    C1 --> C2[2. Supabase Auth 가입<br/>email: seoultech@{eclass_id}<br/>password: {eclass_id}]
    C2 --> C3[3. Supabase users 테이블<br/>암호화된 비밀번호 저장]
    C3 --> C4[4. JWT 토큰 반환]
    
    D --> D1[1. 이클래스 계정 검증<br/>EclassSession.login()]
    D1 --> D2[2. Supabase Auth 로그인<br/>email: seoultech@{eclass_id}<br/>password: {eclass_id}]
    D2 --> D3[3. 이클래스 비밀번호<br/>암호화 업데이트]
    D3 --> D4[4. JWT 토큰 반환]
    
    C4 --> E[클라이언트: JWT 토큰 저장]
    D4 --> E
    
    E --> F[API 요청 시<br/>Authorization: Bearer {jwt_token}]
    F --> G[AuthSessionService.verify_token()]
    G --> H{토큰 유효?}
    
    H -->|Yes| I[사용자 정보 반환<br/>+ eclass_username]
    H -->|No| J[401 Unauthorized]
    
    I --> K[리소스 접근 권한 확인<br/>Supabase RLS 정책]
    K --> L[강의자료 접근 허용]
```

## 🔐 Security Layer Details

### 1. 이클래스 계정 검증
```python
# 실제 이클래스 로그인 시도
eclass_session = EclassSession()
is_valid = await eclass_session.login(eclass_id, eclass_password)
```

### 2. Supabase Auth 통합
```python
# 등록 시
auth_response = supabase.auth.sign_up({
    "email": f"seoultech@{eclass_username}",
    "password": eclass_username  # eclass_id를 Supabase 패스워드로 사용
})

# 로그인 시
auth_response = supabase.auth.sign_in_with_password({
    "email": f"seoultech@{eclass_username}",
    "password": eclass_username
})
```

### 3. 비밀번호 보안
```python
# 암호화 저장
encrypted_password = encrypt_eclass_password(eclass_password)
supabase.table('users').insert({
    'eclass_password': encrypted_password  # AES-256 암호화
})

# 사용 시 복호화
decrypted_password = decrypt_eclass_password(stored_password)
```

### 4. JWT 토큰 검증
```python
# 모든 API 요청마다
user_response = supabase.auth.get_user(jwt_token)
user_info = {
    "id": user_response.user.id,
    "eclass_username": stored_eclass_username
}
```

## 👤 사용자 경험 (UX) 플로우

### 사용자 인식
```
"이클래스에 로그인한다"
↓
이클래스 ID/PW 입력
↓ 
자동으로 강의자료 접근 가능
```

### 실제 기술적 처리
```
이클래스 계정 검증
↓
Supabase 인증 처리 (백그라운드)
↓
JWT 토큰 발급
↓
강의자료 접근 권한 확인
↓
자료 제공
```

## 🚀 API Endpoints

### 회원가입 (사용자에게는 "이클래스 연동"으로 표시)
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "eclass_username": "20241234",
  "eclass_password": "user_password"
}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "refresh_token_here",
  "user": {
    "id": "uuid",
    "eclass_username": "20241234"
  }
}
```

### 로그인 (사용자에게는 "이클래스 접속"으로 표시)
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "eclass_username": "20241234", 
  "eclass_password": "user_password"
}

Response: (동일한 형식)
```

### 토큰 검증
```http
GET /api/v1/auth/verify
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

Response:
{
  "id": "uuid",
  "eclass_username": "20241234",
  "email": "seoultech@20241234"
}
```

### 로그아웃
```http
POST /api/v1/auth/logout
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

Response:
{
  "status": "success",
  "message": "로그아웃되었습니다."
}
```

## 🔄 Session Management

### 세션 유형
1. **Supabase JWT Session**: AutoLMS 서비스 인증용
2. **EclassSession**: 이클래스 크롤링용 HTTP 세션

### 세션 생명주기
```python
# JWT 토큰 (Supabase 관리)
- 발급: AuthService.login/register
- 검증: AuthSessionService.verify_token  
- 갱신: AuthSessionService.refresh_token
- 만료: Supabase Auth 자동 관리

# 이클래스 세션 (EclassSessionManager 관리)  
- 생성: 크롤링 요청 시 자동
- 유지: 쿠키 기반 HTTP 세션
- 만료: 이클래스 서버 정책에 따름
```

## 🛡️ Security Considerations

### 보안 강화 사항
- ✅ 이클래스 비밀번호 AES-256 암호화 저장
- ✅ Supabase JWT 표준 인증 사용
- ✅ 토큰 기반 stateless 인증
- ✅ 자동 토큰 만료 및 갱신 지원

### 향후 보안 개선 계획
- 🔄 키 교체 정책 수립
- 🔄 더 안전한 키 관리 시스템 (HashiCorp Vault 등)
- 🔄 로그인 시도 제한 및 모니터링