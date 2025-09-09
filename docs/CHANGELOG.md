# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - Auth System Refactor

### Added
- AES 암호화 기반 이클래스 비밀번호 보안 시스템
- Supabase JWT 통합 인증 시스템
- 강의자료 공유를 위한 권한 기반 접근 제어 시스템
- Changelog 기반 문서화 시스템

### Changed
- PostgreSQL User 모델 → Supabase 완전 통합
- UUID 임시 토큰 → Supabase JWT 표준 토큰
- 회원가입/로그인 플로우 → 이클래스 계정 연동 방식
- 사용자 경험: AutoLMS 로그인 → 이클래스 접속 인식

### Removed
- PostgreSQL User 모델 및 관련 리포지토리
- 기존 UUID 기반 세션 관리 코드
- 복잡한 이중 저장소 구조

### Security
- 이클래스 비밀번호 AES 암호화 저장 (평문 저장 해결)
- Supabase JWT 표준 인증으로 토큰 보안 강화
- Row Level Security(RLS) 정책 기반 데이터 접근 제어

---

## [Previous] - Before Refactor

### Issues Identified
- 이클래스 비밀번호 평문 저장 (보안 취약점)
- PostgreSQL + Supabase 이중 저장소로 인한 데이터 일관성 문제
- 랜덤 생성 비밀번호로 인한 재로그인 불가 문제
- 복잡한 3중 사용자 관리 구조 (PostgreSQL + Supabase Auth + Supabase Table)