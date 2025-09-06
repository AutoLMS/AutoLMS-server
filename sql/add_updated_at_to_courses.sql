-- courses 테이블에 updated_at 컬럼 추가
ALTER TABLE courses 
ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();

-- 기존 레코드들의 updated_at을 created_at과 동일하게 설정
UPDATE courses 
SET updated_at = created_at 
WHERE updated_at IS NULL;

-- updated_at 컬럼을 NOT NULL로 변경
ALTER TABLE courses 
ALTER COLUMN updated_at SET NOT NULL;

-- 자동 업데이트 트리거 생성
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- courses 테이블에 트리거 적용
CREATE TRIGGER update_courses_updated_at
    BEFORE UPDATE ON courses
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();