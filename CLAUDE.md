# AutoLMS - Claude Development Guide

## 🔧 Development Guidelines

- "필요하다고 생각하면 브랜치를 새로파서 진행해야 합니다."

## 📝 Documentation Rules

### Changelog Management
- **모든 중대한 변경사항은 `docs/CHANGELOG.md`에 기록**
- Keep a Changelog 형식 준수
- 날짜별 변경 이력 관리

### Documentation Structure
```
docs/
├── CHANGELOG.md              # 전체 프로젝트 변경 이력
├── {feature-name}/
│   ├── planning.md          # 기능 계획서
│   ├── implementation.md    # 구현 과정 상세 기록
│   ├── api-changes.md       # API 변경사항
│   └── security-notes.md    # 보안 관련 사항
└── user-flows/             # 사용자 플로우 다이어그램
```

### Documentation Standards
1. **실시간 업데이트**: 구현 과정에서 즉시 문서 업데이트
2. **상세 기록**: 기술적 결정 사항과 근거 명시
3. **변경 추적**: Before/After 상태 명확히 기록
4. **보안 고려사항**: 보안 관련 변경사항 별도 문서화

### Commit Message Convention
- feat: 새로운 기능 추가
- refactor: 코드 리팩토링
- docs: 문서화 관련 변경
- security: 보안 개선사항
- test: 테스트 코드 추가/수정

### API Documentation
- API 변경 시 `{feature-name}/api-changes.md` 업데이트
- Before/After API 스펙 명시
- Breaking changes 명확히 표시

## 🔐 Security Guidelines
- 민감한 정보는 환경변수로 관리
- 암호화 키는 안전한 방식으로 생성 및 보관
- 보안 변경사항은 별도 문서화