-- user_profiles 테이블에 eclass_password 컬럼 추가

ALTER TABLE user_profiles 
ADD COLUMN IF NOT EXISTS eclass_password TEXT;

-- 컬럼에 대한 설명 추가
COMMENT ON COLUMN user_profiles.eclass_password IS 'eClass 계정 비밀번호 (암호화되어 저장됨)';

-- 기존 데이터가 있다면 임시로 환경변수 값으로 업데이트 (실제 운영에서는 사용자별로 다시 설정 필요)
-- UPDATE user_profiles SET eclass_password = '사용자별_실제_비밀번호' WHERE eclass_password IS NULL;