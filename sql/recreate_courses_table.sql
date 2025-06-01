-- courses 테이블 재생성 및 외래 키 종속성 설정
-- Supabase 대시보드 SQL Editor에서 실행하세요

-- 1. courses 테이블 재생성 (course_id를 TEXT 타입으로)
CREATE TABLE courses (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    course_id TEXT NOT NULL UNIQUE,  -- eClass 강의 ID (A2025114608541001 형식)
    course_name TEXT,
    instructor TEXT,
    semester TEXT,
    year TEXT,
    last_crawled TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. 다른 테이블들의 course_id 컬럼을 TEXT로 변경
-- notices 테이블
ALTER TABLE notices 
ALTER COLUMN course_id TYPE TEXT;

-- materials 테이블  
ALTER TABLE materials
ALTER COLUMN course_id TYPE TEXT;

-- assignments 테이블
ALTER TABLE assignments
ALTER COLUMN course_id TYPE TEXT;

-- attachments 테이블
ALTER TABLE attachments
ALTER COLUMN course_id TYPE TEXT;

-- 3. 외래 키 제약 조건 추가 (course_id 참조)
-- notices -> courses.course_id
ALTER TABLE notices 
ADD CONSTRAINT fk_notices_course_id 
FOREIGN KEY (course_id) REFERENCES courses(course_id) 
ON DELETE CASCADE ON UPDATE CASCADE;

-- materials -> courses.course_id
ALTER TABLE materials
ADD CONSTRAINT fk_materials_course_id 
FOREIGN KEY (course_id) REFERENCES courses(course_id) 
ON DELETE CASCADE ON UPDATE CASCADE;

-- assignments -> courses.course_id
ALTER TABLE assignments
ADD CONSTRAINT fk_assignments_course_id 
FOREIGN KEY (course_id) REFERENCES courses(course_id) 
ON DELETE CASCADE ON UPDATE CASCADE;

-- attachments -> courses.course_id
ALTER TABLE attachments
ADD CONSTRAINT fk_attachments_course_id 
FOREIGN KEY (course_id) REFERENCES courses(course_id) 
ON DELETE CASCADE ON UPDATE CASCADE;

-- 4. 인덱스 생성 (성능 향상)
CREATE INDEX IF NOT EXISTS idx_courses_course_id ON courses(course_id);
CREATE INDEX IF NOT EXISTS idx_courses_user_id ON courses(user_id);
CREATE INDEX IF NOT EXISTS idx_notices_course_id ON notices(course_id);
CREATE INDEX IF NOT EXISTS idx_materials_course_id ON materials(course_id);
CREATE INDEX IF NOT EXISTS idx_assignments_course_id ON assignments(course_id);
CREATE INDEX IF NOT EXISTS idx_attachments_course_id ON attachments(course_id);

-- 5. RLS (Row Level Security) 정책 설정
-- courses 테이블 RLS 활성화
ALTER TABLE courses ENABLE ROW LEVEL SECURITY;

-- courses 테이블 정책 생성
CREATE POLICY "Users can manage their own courses" ON courses
FOR ALL USING (auth.uid() = user_id);

-- 6. 확인 쿼리
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'courses'
ORDER BY ordinal_position;

-- 7. 외래 키 제약 조건 확인
SELECT
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    tc.constraint_name
FROM 
    information_schema.table_constraints AS tc 
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
      AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY' 
  AND ccu.table_name = 'courses';

-- 8. 테스트 데이터 삽입 (선택사항)
/*
INSERT INTO courses (user_id, course_id, course_name, instructor, semester, year) 
VALUES 
    ('af56401f-da61-44fb-a201-3bfe163ecee3', 'A2025114608541001', 'IT Project Management', '김교수님', '2025-1학기', '2025'),
    ('af56401f-da61-44fb-a201-3bfe163ecee3', 'A2025114607141001', 'Information Security', '이교수님', '2025-1학기', '2025');
*/