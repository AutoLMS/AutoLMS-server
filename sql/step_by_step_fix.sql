-- 단계별 Supabase 스키마 수정
-- 각 단계를 개별적으로 실행하여 오류 지점을 찾으세요

-- STEP 1: 컬럼 존재 여부 확인
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name IN ('courses', 'notices', 'materials', 'assignments', 'attachments')
ORDER BY table_name, ordinal_position;

-- STEP 2: 필수 컬럼 추가 (하나씩 실행)
-- notices 테이블에 article_id 추가
ALTER TABLE notices ADD COLUMN IF NOT EXISTS article_id VARCHAR;

-- STEP 3: materials 테이블에 article_id 추가  
-- ALTER TABLE materials ADD COLUMN IF NOT EXISTS article_id VARCHAR;

-- STEP 4: assignments 테이블에 article_id 추가
-- ALTER TABLE assignments ADD COLUMN IF NOT EXISTS article_id VARCHAR;

-- STEP 5: course_id 타입 변경 (가장 까다로운 부분)
-- 먼저 courses 테이블의 course_id 확인
-- SELECT course_id, pg_typeof(course_id) FROM courses LIMIT 5;

-- STEP 6: 만약 course_id가 정수라면 문자열로 변환
-- ALTER TABLE courses ALTER COLUMN course_id TYPE VARCHAR USING course_id::VARCHAR;

-- STEP 7: 다른 테이블들도 순차적으로 변경
-- ALTER TABLE notices ALTER COLUMN course_id TYPE VARCHAR USING course_id::VARCHAR;
-- ALTER TABLE materials ALTER COLUMN course_id TYPE VARCHAR USING course_id::VARCHAR;
-- ALTER TABLE assignments ALTER COLUMN course_id TYPE VARCHAR USING course_id::VARCHAR;
-- ALTER TABLE attachments ALTER COLUMN course_id TYPE VARCHAR USING course_id::VARCHAR;