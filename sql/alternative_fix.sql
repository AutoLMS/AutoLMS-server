-- 대안 방법: 외래 키 제약 조건이 있는 경우의 해결책

-- 1. 먼저 외래 키 제약 조건 확인
SELECT
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM 
    information_schema.table_constraints AS tc 
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
      AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY';

-- 2. 외래 키 제약 조건 삭제 (필요한 경우)
-- ALTER TABLE notices DROP CONSTRAINT IF EXISTS notices_course_id_fkey;
-- ALTER TABLE materials DROP CONSTRAINT IF EXISTS materials_course_id_fkey;
-- ALTER TABLE assignments DROP CONSTRAINT IF EXISTS assignments_course_id_fkey;

-- 3. 컬럼 타입 변경
-- ALTER TABLE courses ALTER COLUMN course_id TYPE VARCHAR USING course_id::VARCHAR;
-- ALTER TABLE notices ALTER COLUMN course_id TYPE VARCHAR USING course_id::VARCHAR;
-- ALTER TABLE materials ALTER COLUMN course_id TYPE VARCHAR USING course_id::VARCHAR;
-- ALTER TABLE assignments ALTER COLUMN course_id TYPE VARCHAR USING course_id::VARCHAR;

-- 4. 필수 컬럼 추가
-- ALTER TABLE notices ADD COLUMN IF NOT EXISTS article_id VARCHAR;
-- ALTER TABLE materials ADD COLUMN IF NOT EXISTS article_id VARCHAR;
-- ALTER TABLE assignments ADD COLUMN IF NOT EXISTS article_id VARCHAR;

-- 5. 외래 키 제약 조건 재생성 (필요한 경우)
-- ALTER TABLE notices ADD CONSTRAINT notices_course_id_fkey FOREIGN KEY (course_id) REFERENCES courses(course_id);
-- ALTER TABLE materials ADD CONSTRAINT materials_course_id_fkey FOREIGN KEY (course_id) REFERENCES courses(course_id);
-- ALTER TABLE assignments ADD CONSTRAINT assignments_course_id_fkey FOREIGN KEY (course_id) REFERENCES courses(course_id);