-- 기존 데이터가 있는 경우의 마이그레이션
-- 주의: 기존 데이터를 백업한 후 실행하세요!

-- 1. 기존 데이터 백업 (선택사항)
-- CREATE TABLE notices_backup AS SELECT * FROM notices;
-- CREATE TABLE materials_backup AS SELECT * FROM materials;
-- CREATE TABLE assignments_backup AS SELECT * FROM assignments;
-- CREATE TABLE attachments_backup AS SELECT * FROM attachments;

-- 2. 외래 키 제약 조건 삭제 (있다면)
ALTER TABLE notices DROP CONSTRAINT IF EXISTS notices_course_id_fkey;
ALTER TABLE notices DROP CONSTRAINT IF EXISTS fk_notices_course_id;

ALTER TABLE materials DROP CONSTRAINT IF EXISTS materials_course_id_fkey;
ALTER TABLE materials DROP CONSTRAINT IF EXISTS fk_materials_course_id;

ALTER TABLE assignments DROP CONSTRAINT IF EXISTS assignments_course_id_fkey;
ALTER TABLE assignments DROP CONSTRAINT IF EXISTS fk_assignments_course_id;

ALTER TABLE attachments DROP CONSTRAINT IF EXISTS attachments_course_id_fkey;
ALTER TABLE attachments DROP CONSTRAINT IF EXISTS fk_attachments_course_id;

-- 3. course_id 컬럼 타입을 TEXT로 변경
ALTER TABLE notices 
ALTER COLUMN course_id TYPE TEXT USING course_id::TEXT;

ALTER TABLE materials
ALTER COLUMN course_id TYPE TEXT USING course_id::TEXT;

ALTER TABLE assignments
ALTER COLUMN course_id TYPE TEXT USING course_id::TEXT;

ALTER TABLE attachments
ALTER COLUMN course_id TYPE TEXT USING course_id::TEXT;

-- 4. 누락된 컬럼 추가
ALTER TABLE notices 
ADD COLUMN IF NOT EXISTS article_id TEXT,
ADD COLUMN IF NOT EXISTS author TEXT,
ADD COLUMN IF NOT EXISTS date TEXT,
ADD COLUMN IF NOT EXISTS views INTEGER DEFAULT 0;

ALTER TABLE materials
ADD COLUMN IF NOT EXISTS article_id TEXT,
ADD COLUMN IF NOT EXISTS author TEXT,
ADD COLUMN IF NOT EXISTS date TEXT,
ADD COLUMN IF NOT EXISTS views INTEGER DEFAULT 0;

ALTER TABLE assignments
ADD COLUMN IF NOT EXISTS article_id TEXT;

ALTER TABLE attachments
ADD COLUMN IF NOT EXISTS file_name TEXT,
ADD COLUMN IF NOT EXISTS original_url TEXT,
ADD COLUMN IF NOT EXISTS storage_path TEXT DEFAULT '';

-- 5. courses 테이블 재생성 (위의 recreate_courses_table.sql 참조)
-- 이미 실행했다면 생략

-- 6. 외래 키 제약 조건 재생성 (courses 테이블 생성 후)
ALTER TABLE notices 
ADD CONSTRAINT fk_notices_course_id 
FOREIGN KEY (course_id) REFERENCES courses(course_id) 
ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE materials
ADD CONSTRAINT fk_materials_course_id 
FOREIGN KEY (course_id) REFERENCES courses(course_id) 
ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE assignments
ADD CONSTRAINT fk_assignments_course_id 
FOREIGN KEY (course_id) REFERENCES courses(course_id) 
ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE attachments
ADD CONSTRAINT fk_attachments_course_id 
FOREIGN KEY (course_id) REFERENCES courses(course_id) 
ON DELETE CASCADE ON UPDATE CASCADE;