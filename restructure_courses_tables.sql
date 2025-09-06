-- 새로운 효율적인 강의 구조 생성
-- 1. courses 테이블 구조 변경 (user_id 제거, course_id를 primary key로)
-- 2. user_courses 매핑 테이블 생성

-- 기존 courses 테이블 백업
CREATE TABLE courses_backup AS 
SELECT * FROM courses;

-- 기존 courses 테이블 삭제
DROP TABLE IF EXISTS courses CASCADE;

-- 새로운 courses 테이블 (강의 정보만)
CREATE TABLE courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id VARCHAR(255) UNIQUE NOT NULL, -- eClass 강의 ID (unique)
    course_name TEXT NOT NULL,
    instructor VARCHAR(255),
    semester VARCHAR(100),
    year INTEGER,
    description TEXT,
    last_crawled TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 새로운 user_courses 매핑 테이블 (사용자-강의 관계)
CREATE TABLE IF NOT EXISTS user_courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    course_id VARCHAR(255) REFERENCES courses(course_id) ON DELETE CASCADE NOT NULL,
    enrollment_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- user_id + course_id 조합이 unique해야 함
    UNIQUE(user_id, course_id)
);

-- courses 테이블에 업데이트 트리거 추가
CREATE OR REPLACE FUNCTION update_courses_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_courses_updated_at
    BEFORE UPDATE ON courses
    FOR EACH ROW
    EXECUTE FUNCTION update_courses_updated_at();

-- user_courses 테이블에 업데이트 트리거 추가
CREATE OR REPLACE FUNCTION update_user_courses_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_courses_updated_at
    BEFORE UPDATE ON user_courses
    FOR EACH ROW
    EXECUTE FUNCTION update_user_courses_updated_at();

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_courses_course_id ON courses(course_id);
CREATE INDEX IF NOT EXISTS idx_user_courses_user_id ON user_courses(user_id);
CREATE INDEX IF NOT EXISTS idx_user_courses_course_id ON user_courses(course_id);
CREATE INDEX IF NOT EXISTS idx_user_courses_user_course ON user_courses(user_id, course_id);

-- RLS (Row Level Security) 활성화
ALTER TABLE courses ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_courses ENABLE ROW LEVEL SECURITY;

-- courses 테이블 RLS 정책 (모든 사용자가 읽기 가능, 관리자만 쓰기)
CREATE POLICY "Anyone can view courses" ON courses
    FOR SELECT USING (true);

CREATE POLICY "Service role can manage courses" ON courses
    FOR ALL USING (auth.role() = 'service_role');

-- user_courses 테이블 RLS 정책 (사용자는 자신의 강의만 접근)
CREATE POLICY "Users can view own course enrollments" ON user_courses
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own course enrollments" ON user_courses
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own course enrollments" ON user_courses
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own course enrollments" ON user_courses
    FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Service role can manage user_courses" ON user_courses
    FOR ALL USING (auth.role() = 'service_role');

-- 기존 데이터를 새 구조로 마이그레이션
-- 1. 중복 제거하여 courses 테이블에 강의 정보 삽입
INSERT INTO courses (course_id, course_name, instructor, semester, year, last_crawled, created_at, updated_at)
SELECT DISTINCT 
    course_id,
    course_name,
    instructor,
    semester,
    CASE 
        WHEN year ~ '^[0-9]+$' THEN year::INTEGER 
        ELSE NULL 
    END as year,  -- TEXT를 INTEGER로 안전하게 변환
    last_crawled,
    created_at,
    updated_at
FROM courses_backup
ON CONFLICT (course_id) DO UPDATE SET
    course_name = EXCLUDED.course_name,
    instructor = EXCLUDED.instructor,
    semester = EXCLUDED.semester,
    year = EXCLUDED.year,
    last_crawled = EXCLUDED.last_crawled,
    updated_at = EXCLUDED.updated_at;

-- 2. 사용자-강의 매핑 정보를 user_courses에 삽입
INSERT INTO user_courses (user_id, course_id, created_at, updated_at)
SELECT DISTINCT 
    user_id,
    course_id,
    created_at,
    updated_at
FROM courses_backup
ON CONFLICT (user_id, course_id) DO NOTHING;

-- 테이블에 코멘트 추가
COMMENT ON TABLE courses IS 'Course information without user-specific data';
COMMENT ON TABLE user_courses IS 'User-course enrollment mapping table';

-- 백업 테이블 삭제 (선택사항, 안전을 위해 보관할 수도 있음)
-- DROP TABLE courses_backup;