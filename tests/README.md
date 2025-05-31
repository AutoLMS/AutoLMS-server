# Tests

이 폴더는 다양한 테스트 파일들을 포함합니다.

## 파일 설명

### 데이터베이스 테스트
- `test_db_connection.py` - 기본 DB 연결 테스트
- `test_db_connection_fixed.py` - 수정된 DB 연결 테스트

### Supabase 테스트
- `test_supabase_connection.py` - Supabase 연결 테스트
- `test_supabase_storage.py` - Supabase 스토리지 테스트
- `test_corrected_storage.py` - 수정된 스토리지 테스트
- `test_material_supabase.py` - 강의자료 Supabase 연동 테스트
- `test_rls_policies.py` - RLS 정책 테스트

### 크롤링 테스트
- `test_eclass_direct.py` - eClass 직접 연결 테스트
- `test_real_crawling.py` - 실제 크롤링 테스트
- `test_simple_crawling.py` - 간단 크롤링 테스트
- `test_production_crawling.py` - 프로덕션 크롤링 테스트

### 파일 처리 테스트
- `test_file_download_upload.py` - 파일 업다운로드 테스트
- `test_material_download.py` - 강의자료 다운로드 테스트

## 사용법

```bash
# 특정 테스트 실행
python tests/test_db_connection.py

# 모든 테스트 실행 (pytest 사용)
pytest tests/
```