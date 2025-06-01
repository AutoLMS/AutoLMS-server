-- 간단한 Supabase 스키마 수정 (최소한의 변경)
-- 기존 코드와 호환되도록 필수 컬럼만 추가

-- 실행 전 확인사항:
-- 1. 기존 데이터 백업
-- 2. Supabase 대시보드에서 실행
-- 3. RLS 정책 확인

-- 1. notices 테이블에 필수 컬럼 추가
ALTER TABLE notices 
ADD COLUMN IF NOT EXISTS article_id VARCHAR,
ADD COLUMN IF NOT EXISTS author VARCHAR,
ADD COLUMN IF NOT EXISTS date VARCHAR,
ADD COLUMN IF NOT EXISTS views INTEGER DEFAULT 0;

-- 2. materials 테이블에 필수 컬럼 추가  
ALTER TABLE materials
ADD COLUMN IF NOT EXISTS article_id VARCHAR,
ADD COLUMN IF NOT EXISTS author VARCHAR,
ADD COLUMN IF NOT EXISTS date VARCHAR,
ADD COLUMN IF NOT EXISTS views INTEGER DEFAULT 0;

-- 3. assignments 테이블에 필수 컬럼 추가
ALTER TABLE assignments
ADD COLUMN IF NOT EXISTS article_id VARCHAR,
ADD COLUMN IF NOT EXISTS author VARCHAR,
ADD COLUMN IF NOT EXISTS date VARCHAR,
ADD COLUMN IF NOT EXISTS views INTEGER DEFAULT 0;

-- 4. attachments 테이블에 필수 컬럼 추가
ALTER TABLE attachments
ADD COLUMN IF NOT EXISTS file_name VARCHAR,
ADD COLUMN IF NOT EXISTS original_url VARCHAR,
ADD COLUMN IF NOT EXISTS storage_path VARCHAR DEFAULT '';

-- 5. courses 테이블 course_id 타입 확인 및 수정
-- (course_id가 정수라면 문자열로 변경)
ALTER TABLE courses 
ALTER COLUMN course_id TYPE VARCHAR USING course_id::VARCHAR;

-- 6. 인덱스 추가 (성능 향상)
CREATE INDEX IF NOT EXISTS idx_notices_article_id ON notices(article_id);
CREATE INDEX IF NOT EXISTS idx_materials_article_id ON materials(article_id);
CREATE INDEX IF NOT EXISTS idx_assignments_article_id ON assignments(article_id);

-- 7. 스키마 확인
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name IN ('notices', 'materials', 'assignments', 'attachments', 'courses')
  AND column_name IN ('article_id', 'author', 'date', 'views', 'file_name', 'original_url', 'storage_path', 'course_id')
ORDER BY table_name, column_name;