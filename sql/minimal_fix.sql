-- 최소한의 Supabase 스키마 수정
-- Supabase 대시보드 SQL Editor에서 실행하세요

-- 1. 필수 컬럼 추가 (누락된 컬럼들)
ALTER TABLE notices 
ADD COLUMN IF NOT EXISTS article_id VARCHAR;

ALTER TABLE materials
ADD COLUMN IF NOT EXISTS article_id VARCHAR;

ALTER TABLE assignments
ADD COLUMN IF NOT EXISTS article_id VARCHAR;

-- 2. courses 테이블의 course_id를 VARCHAR로 변경
ALTER TABLE courses 
ALTER COLUMN course_id TYPE VARCHAR;

-- 3. 다른 테이블의 course_id도 VARCHAR로 변경
ALTER TABLE notices 
ALTER COLUMN course_id TYPE VARCHAR;

ALTER TABLE materials 
ALTER COLUMN course_id TYPE VARCHAR;

ALTER TABLE assignments 
ALTER COLUMN course_id TYPE VARCHAR;

ALTER TABLE attachments 
ALTER COLUMN course_id TYPE VARCHAR;

-- 확인
SELECT table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_name IN ('courses', 'notices', 'materials', 'assignments') 
  AND column_name IN ('course_id', 'article_id')
ORDER BY table_name, column_name;