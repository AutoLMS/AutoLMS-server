-- Supabase에서 이메일 확인을 비활성화하는 SQL

-- 1. 기존 사용자의 이메일 확인 상태 업데이트
UPDATE auth.users 
SET email_confirmed_at = NOW(),
    confirmed_at = NOW()
WHERE email_confirmed_at IS NULL;

-- 2. 특정 테스트 사용자 활성화
UPDATE auth.users 
SET email_confirmed_at = NOW(),
    confirmed_at = NOW()
WHERE email = 'testuser123@gmail.com';

-- 3. 사용자 상태 확인
SELECT id, email, email_confirmed_at, confirmed_at, created_at 
FROM auth.users 
ORDER BY created_at DESC;
