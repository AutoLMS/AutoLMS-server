-- Supabase에서 이메일 확인 비활성화 및 사용자 활성화

-- 특정 사용자의 이메일 확인 상태 업데이트
UPDATE auth.users 
SET email_confirmed_at = NOW(),
    confirmed_at = NOW()
WHERE email = 'testuser123@gmail.com';

-- 모든 신규 사용자의 이메일 자동 확인 설정 (선택사항)
-- UPDATE auth.users 
-- SET email_confirmed_at = NOW(),
--     confirmed_at = NOW()
-- WHERE email_confirmed_at IS NULL;

-- 사용자 상태 확인
SELECT id, email, email_confirmed_at, confirmed_at, created_at 
FROM auth.users 
WHERE email = 'testuser123@gmail.com';
