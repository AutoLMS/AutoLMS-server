# Scripts

이 폴더는 프로젝트 설정, 마이그레이션, 분석을 위한 스크립트들을 포함합니다.

## 파일 설명

### 설정 스크립트
- `setup_supabase_storage.py` - Supabase 스토리지 초기 설정
- `migrate_attachments.py` - 첨부파일 마이그레이션

### 사용자 관리 스크립트
- `create_test_user.py` - 테스트 사용자 생성
- `activate_user.py` - 일반 사용자 활성화
- `activate_current_user.py` - 현재 사용자 활성화
- `activate_admin.py` - 관리자 권한 활성화

### 분석 스크립트
- `analyze_eclass.py` - eClass 페이지 구조 분석
- `find_attachments.py` - 첨부파일 찾기 및 분석
- `crawl_test_data.py` - 크롤링 테스트 데이터 생성

## 사용법

```bash
# 예: Supabase 스토리지 설정
python scripts/setup_supabase_storage.py

# 예: 테스트 사용자 생성
python scripts/create_test_user.py

# 예: eClass 구조 분석
python scripts/analyze_eclass.py
```