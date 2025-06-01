-- 누락된 컬럼들 추가
-- recreate_courses_table.sql 실행 후에 이 스크립트를 실행하세요

-- 1. notices 테이블에 누락된 컬럼 추가
ALTER TABLE notices 
ADD COLUMN IF NOT EXISTS article_id TEXT,
ADD COLUMN IF NOT EXISTS author TEXT,
ADD COLUMN IF NOT EXISTS date TEXT,
ADD COLUMN IF NOT EXISTS views INTEGER DEFAULT 0;

-- 2. materials 테이블에 누락된 컬럼 추가
ALTER TABLE materials
ADD COLUMN IF NOT EXISTS article_id TEXT,
ADD COLUMN IF NOT EXISTS author TEXT,
ADD COLUMN IF NOT EXISTS date TEXT,
ADD COLUMN IF NOT EXISTS views INTEGER DEFAULT 0;

-- 3. assignments 테이블에 누락된 컬럼 추가
ALTER TABLE assignments
ADD COLUMN IF NOT EXISTS article_id TEXT,
ADD COLUMN IF NOT EXISTS author TEXT,
ADD COLUMN IF NOT EXISTS date TEXT,
ADD COLUMN IF NOT EXISTS views INTEGER DEFAULT 0;

-- 4. attachments 테이블에 누락된 컬럼 추가
ALTER TABLE attachments
ADD COLUMN IF NOT EXISTS file_name TEXT,
ADD COLUMN IF NOT EXISTS original_url TEXT,
ADD COLUMN IF NOT EXISTS storage_path TEXT DEFAULT '';

-- 5. 인덱스 추가 (성능 향상)
CREATE INDEX IF NOT EXISTS idx_notices_article_id ON notices(article_id);
CREATE INDEX IF NOT EXISTS idx_materials_article_id ON materials(article_id);
CREATE INDEX IF NOT EXISTS idx_assignments_article_id ON assignments(article_id);

-- 6. 최종 스키마 확인
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name IN ('courses', 'notices', 'materials', 'assignments', 'attachments')
ORDER BY table_name, ordinal_position;