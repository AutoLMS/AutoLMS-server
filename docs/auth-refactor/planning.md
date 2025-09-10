# Auth System Refactor - Planning Document

## 📋 Project Overview
**Project**: AutoLMS 인증 시스템 전면 개선
**Start Date**: 2025-09-09
**Status**: In Progress

## 🎯 Core Objectives

### Primary Goals
1. **Simplified User Experience**: 이클래스 ID/PW만으로 원클릭 접속
2. **Unified Data Storage**: PostgreSQL → Supabase 완전 통합  
3. **Enhanced Security**: AES 암호화 + JWT 표준 인증
4. **Scalable Architecture**: 강의자료 공유를 위한 권한 시스템

### User Experience Vision
```
사용자 인식: "이클래스에 접속한다"
실제 동작: "AutoLMS 서비스를 통해 이클래스 기능을 사용한다"
```

## 🔧 Technical Architecture

### Current Issues
- **Security**: 이클래스 비밀번호 평문 저장
- **Complexity**: 3중 사용자 관리 (PostgreSQL + Supabase Auth + Supabase Table)
- **Consistency**: 이중 저장소로 인한 데이터 동기화 문제
- **UX**: 랜덤 비밀번호로 인한 재로그인 불가

### Target Architecture
```
Single Source of Truth: Supabase
├── Auth: Supabase JWT 인증
├── Data: Supabase 테이블
└── Security: AES 암호화 + RLS 정책
```

## 📊 Implementation Phases

### Phase 0: Documentation & Security Setup
- [x] Create documentation structure
- [ ] Generate ECLASS_ENCRYPTION_KEY
- [ ] Update CLAUDE.md with documentation rules

### Phase 1: Core Refactoring
- [ ] Remove PostgreSQL User model
- [ ] Implement encryption utilities
- [ ] Refactor auth service

### Phase 2: JWT Integration  
- [ ] Replace UUID tokens with Supabase JWT
- [ ] Update session management
- [ ] Implement token refresh logic

### Phase 3: Permission System
- [ ] Setup Supabase RLS policies
- [ ] Test course material access control
- [ ] Validate multi-user access scenarios

## 🔐 Security Considerations

### Encryption Strategy
- **Algorithm**: AES-256 (Fernet)
- **Key Source**: ECLASS_ENCRYPTION_KEY environment variable
- **Key Storage**: Secure environment variable management

### Authentication Flow
```
Eclass ID/PW → Validation → Supabase Auth → JWT Token → Resource Access
```

## 📈 Success Metrics

### Technical Metrics
- [ ] Single database (Supabase only)
- [ ] 100% encrypted sensitive data
- [ ] JWT standard compliance
- [ ] Zero data synchronization issues

### User Experience Metrics
- [ ] One-step login process
- [ ] Transparent eclass integration
- [ ] Shared course material access
- [ ] No separate account management

## 🚨 Risk Assessment

### High Risk
- Data migration from PostgreSQL to Supabase
- Encryption key management
- Backward compatibility with existing sessions

### Mitigation Strategies
- Comprehensive testing before production deployment
- Secure key generation and storage procedures
- Gradual rollout with rollback capabilities

## 📚 Related Documentation
- [Implementation Notes](./implementation.md)
- [API Changes](./api-changes.md) 
- [Security Notes](./security-notes.md)
- [User Flow Diagrams](../user-flows/auth-flow.md)