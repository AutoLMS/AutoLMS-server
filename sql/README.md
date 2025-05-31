# SQL Scripts

이 폴더는 데이터베이스 설정 및 수정을 위한 SQL 스크립트들을 포함합니다.

## 파일 설명

- `supabase_update.sql` - Supabase 데이터베이스 업데이트 스크립트
- `fix_user_email_confirmation.sql` - 사용자 이메일 확인 수정 스크립트
- `disable_email_confirmation.sql` - 이메일 확인 비활성화 스크립트

## 사용법

```bash
# psql을 통한 실행
psql -h your_host -U your_user -d your_db -f sql/supabase_update.sql

# Supabase CLI를 통한 실행
supabase db reset --linked
```

## 주의사항

- 프로덕션 환경에서 실행하기 전에 반드시 백업을 수행하세요
- 각 스크립트는 단계별로 실행하는 것을 권장합니다