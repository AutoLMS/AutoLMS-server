-- Supabase 테이블 스키마를 Alembic 마이그레이션과 일치시키는 SQL
-- 실행 전에 기존 데이터를 백업하세요!

-- 1. 기존 테이블 백업 (선택사항)
-- CREATE TABLE notices_backup AS SELECT * FROM notices;
-- CREATE TABLE materials_backup AS SELECT * FROM materials;
-- CREATE TABLE assignments_backup AS SELECT * FROM assignments;
-- CREATE TABLE attachments_backup AS SELECT * FROM attachments;

-- 2. courses 테이블 수정 (course_id 컬럼을 문자열로 변경)
BEGIN;

-- courses 테이블의 id를 문자열로 변경하고 course_id 컬럼 추가
ALTER TABLE courses 
DROP CONSTRAINT IF EXISTS courses_pkey;

-- 기존 id 컬럼을 문자열로 변경
ALTER TABLE courses 
ALTER COLUMN id TYPE VARCHAR USING CONCAT('course_', id::text);

-- course_id 컬럼 추가 (없는 경우)
ALTER TABLE courses 
ADD COLUMN IF NOT EXISTS course_id VARCHAR;

-- course_name 컬럼 추가 (없는 경우) 
ALTER TABLE courses 
ADD COLUMN IF NOT EXISTS course_name VARCHAR;

-- 기존 name을 course_name으로 복사
UPDATE courses SET course_name = name WHERE course_name IS NULL;

-- instructor, semester, year, last_crawled 컬럼 추가
ALTER TABLE courses 
ADD COLUMN IF NOT EXISTS instructor VARCHAR,
ADD COLUMN IF NOT EXISTS semester VARCHAR, 
ADD COLUMN IF NOT EXISTS year VARCHAR,
ADD COLUMN IF NOT EXISTS last_crawled TIMESTAMP;

-- 기본 키 재설정
ALTER TABLE courses 
ADD CONSTRAINT courses_pkey PRIMARY KEY (id);

COMMIT;

-- 3. notices 테이블 수정
BEGIN;

-- article_id 컬럼 추가 (notice_id를 article_id로 변경)
ALTER TABLE notices 
ADD COLUMN IF NOT EXISTS article_id VARCHAR;

-- 기존 notice_id 데이터를 article_id로 복사
UPDATE notices SET article_id = notice_id WHERE article_id IS NULL;

-- article_id를 NOT NULL로 설정
ALTER TABLE notices 
ALTER COLUMN article_id SET NOT NULL;

-- course_id를 문자열로 변경
ALTER TABLE notices 
ALTER COLUMN course_id TYPE VARCHAR USING CONCAT('course_', course_id::text);

-- author, date, views 컬럼 추가
ALTER TABLE notices 
ADD COLUMN IF NOT EXISTS author VARCHAR,
ADD COLUMN IF NOT EXISTS date VARCHAR,
ADD COLUMN IF NOT EXISTS views INTEGER DEFAULT 0;

-- 외래 키 제약 조건 재설정
ALTER TABLE notices 
DROP CONSTRAINT IF EXISTS notices_course_id_fkey;

ALTER TABLE notices 
ADD CONSTRAINT notices_course_id_fkey 
FOREIGN KEY (course_id) REFERENCES courses(id);

COMMIT;

-- 4. materials 테이블 수정
BEGIN;

-- article_id 컬럼 추가 (material_id를 article_id로 변경)
ALTER TABLE materials 
ADD COLUMN IF NOT EXISTS article_id VARCHAR;

-- 기존 material_id 데이터를 article_id로 복사
UPDATE materials SET article_id = material_id WHERE article_id IS NULL;

-- article_id를 NOT NULL로 설정
ALTER TABLE materials 
ALTER COLUMN article_id SET NOT NULL;

-- course_id를 문자열로 변경
ALTER TABLE materials 
ALTER COLUMN course_id TYPE VARCHAR USING CONCAT('course_', course_id::text);

-- author, date, views 컬럼 추가
ALTER TABLE materials 
ADD COLUMN IF NOT EXISTS author VARCHAR,
ADD COLUMN IF NOT EXISTS date VARCHAR,
ADD COLUMN IF NOT EXISTS views INTEGER DEFAULT 0;

-- 외래 키 제약 조건 재설정
ALTER TABLE materials 
DROP CONSTRAINT IF EXISTS materials_course_id_fkey;

ALTER TABLE materials 
ADD CONSTRAINT materials_course_id_fkey 
FOREIGN KEY (course_id) REFERENCES courses(id);

COMMIT;

-- 5. assignments 테이블 수정
BEGIN;

-- article_id 컬럼 추가 (assignment_id를 article_id로 변경)
ALTER TABLE assignments 
ADD COLUMN IF NOT EXISTS article_id VARCHAR;

-- 기존 assignment_id 데이터를 article_id로 복사  
UPDATE assignments SET article_id = assignment_id WHERE article_id IS NULL;

-- article_id를 NOT NULL로 설정
ALTER TABLE assignments 
ALTER COLUMN article_id SET NOT NULL;

-- course_id를 문자열로 변경
ALTER TABLE assignments 
ALTER COLUMN course_id TYPE VARCHAR USING CONCAT('course_', course_id::text);

-- author, date, views 컬럼 추가 (assignments에는 다른 필드들이 있을 수 있음)
ALTER TABLE assignments 
ADD COLUMN IF NOT EXISTS author VARCHAR,
ADD COLUMN IF NOT EXISTS date VARCHAR,
ADD COLUMN IF NOT EXISTS views INTEGER DEFAULT 0;

-- 외래 키 제약 조건 재설정
ALTER TABLE assignments 
DROP CONSTRAINT IF EXISTS assignments_course_id_fkey;

ALTER TABLE assignments 
ADD CONSTRAINT assignments_course_id_fkey 
FOREIGN KEY (course_id) REFERENCES courses(id);

COMMIT;

-- 6. attachments 테이블 수정
BEGIN;

-- course_id를 문자열로 변경
ALTER TABLE attachments 
ALTER COLUMN course_id TYPE VARCHAR USING CONCAT('course_', course_id::text);

-- 필요한 컬럼들 추가
ALTER TABLE attachments 
ADD COLUMN IF NOT EXISTS file_name VARCHAR,
ADD COLUMN IF NOT EXISTS original_url VARCHAR,
ADD COLUMN IF NOT EXISTS storage_path VARCHAR;

-- file_name을 NOT NULL로 설정하기 전에 기본값 설정
UPDATE attachments SET file_name = 'unknown_file' WHERE file_name IS NULL;

ALTER TABLE attachments 
ALTER COLUMN file_name SET NOT NULL;

-- storage_path를 NOT NULL로 설정하기 전에 기본값 설정  
UPDATE attachments SET storage_path = '/temp/' WHERE storage_path IS NULL;

ALTER TABLE attachments 
ALTER COLUMN storage_path SET NOT NULL;

COMMIT;

-- 7. 인덱스 생성 (성능 향상)
CREATE INDEX IF NOT EXISTS idx_notices_course_id ON notices(course_id);
CREATE INDEX IF NOT EXISTS idx_notices_article_id ON notices(article_id);
CREATE INDEX IF NOT EXISTS idx_materials_course_id ON materials(course_id);
CREATE INDEX IF NOT EXISTS idx_materials_article_id ON materials(article_id);
CREATE INDEX IF NOT EXISTS idx_assignments_course_id ON assignments(course_id);
CREATE INDEX IF NOT EXISTS idx_assignments_article_id ON assignments(article_id);
CREATE INDEX IF NOT EXISTS idx_attachments_course_id ON attachments(course_id);
CREATE INDEX IF NOT EXISTS idx_courses_course_id ON courses(course_id);

-- 8. RLS (Row Level Security) 정책 확인 및 조정
-- 필요에 따라 RLS 정책을 조정하세요
-- 예시:
/*
-- notices 테이블 RLS 정책
DROP POLICY IF EXISTS "notices_policy" ON notices;
CREATE POLICY "notices_policy" ON notices
FOR ALL USING (auth.uid()::text = user_id);

-- materials 테이블 RLS 정책  
DROP POLICY IF EXISTS "materials_policy" ON materials;
CREATE POLICY "materials_policy" ON materials
FOR ALL USING (auth.uid()::text = user_id);

-- assignments 테이블 RLS 정책
DROP POLICY IF EXISTS "assignments_policy" ON assignments;
CREATE POLICY "assignments_policy" ON assignments
FOR ALL USING (auth.uid()::text = user_id);

-- attachments 테이블 RLS 정책
DROP POLICY IF EXISTS "attachments_policy" ON attachments;
CREATE POLICY "attachments_policy" ON attachments
FOR ALL USING (auth.uid()::text = user_id);

-- courses 테이블 RLS 정책
DROP POLICY IF EXISTS "courses_policy" ON courses;
CREATE POLICY "courses_policy" ON courses
FOR ALL USING (auth.uid()::text = user_id);
*/

-- 9. 스키마 변경 완료 확인
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name IN ('courses', 'notices', 'materials', 'assignments', 'attachments')
ORDER BY table_name, ordinal_position;