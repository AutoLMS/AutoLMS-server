-- Supabase 스키마 수정 SQL
-- 누락된 컬럼들 추가 및 외래키 관계 설정

-- 1. materials 테이블에 has_attachments 컬럼 추가
ALTER TABLE materials 
ADD COLUMN IF NOT EXISTS has_attachments BOOLEAN DEFAULT FALSE;

-- 2. attachments 테이블에 누락된 컬럼들 추가
ALTER TABLE attachments 
ADD COLUMN IF NOT EXISTS source_id TEXT,
ADD COLUMN IF NOT EXISTS source_type TEXT,
ADD COLUMN IF NOT EXISTS user_id TEXT;

-- 기존 parent_id, parent_type 컬럼이 있다면 데이터 마이그레이션
-- (있을 경우에만 실행)
DO $$ 
BEGIN
    -- parent_id -> source_id 데이터 마이그레이션
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name='attachments' AND column_name='parent_id') THEN
        UPDATE attachments SET source_id = parent_id WHERE source_id IS NULL;
    END IF;
    
    -- parent_type -> source_type 데이터 마이그레이션  
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name='attachments' AND column_name='parent_type') THEN
        UPDATE attachments SET source_type = parent_type WHERE source_type IS NULL;
    END IF;
END $$;

-- 3. assignments 테이블에 누락된 컬럼들 추가
ALTER TABLE assignments 
ADD COLUMN IF NOT EXISTS author TEXT,
ADD COLUMN IF NOT EXISTS start_date TEXT,
ADD COLUMN IF NOT EXISTS end_date TEXT,
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active';

-- 4. 외래키 제약조건 추가 (선택사항 - 성능상 문제가 있을 수 있음)
-- attachments -> materials 관계
-- ALTER TABLE attachments 
-- ADD CONSTRAINT fk_attachments_materials 
-- FOREIGN KEY (source_id) REFERENCES materials(id) 
-- ON DELETE CASCADE;

-- 5. 인덱스 추가 (성능 향상)
CREATE INDEX IF NOT EXISTS idx_attachments_source 
ON attachments(source_id, source_type);

CREATE INDEX IF NOT EXISTS idx_materials_course 
ON materials(course_id);

CREATE INDEX IF NOT EXISTS idx_materials_article 
ON materials(article_id);

-- 6. 기존 materials 데이터에 has_attachments 값 업데이트
UPDATE materials 
SET has_attachments = (
    SELECT COUNT(*) > 0 
    FROM attachments 
    WHERE attachments.source_id::text = materials.id::text 
    AND attachments.source_type = 'lecture_materials'
);

-- 7. RLS (Row Level Security) 정책 업데이트 (필요시)
-- ALTER TABLE attachments ENABLE ROW LEVEL SECURITY;

-- 8. 트리거 생성 - materials에 첨부파일이 추가/삭제될 때 has_attachments 자동 업데이트
CREATE OR REPLACE FUNCTION update_material_attachments()
RETURNS TRIGGER AS $$
BEGIN
    -- INSERT/UPDATE 시
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        UPDATE materials 
        SET has_attachments = TRUE 
        WHERE id::text = NEW.source_id AND NEW.source_type = 'lecture_materials';
        RETURN NEW;
    END IF;
    
    -- DELETE 시
    IF TG_OP = 'DELETE' THEN
        UPDATE materials 
        SET has_attachments = (
            SELECT COUNT(*) > 0 
            FROM attachments 
            WHERE source_id::text = OLD.source_id 
            AND source_type = 'lecture_materials'
        )
        WHERE id::text = OLD.source_id;
        RETURN OLD;
    END IF;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- 트리거 생성
DROP TRIGGER IF EXISTS trigger_update_material_attachments ON attachments;
CREATE TRIGGER trigger_update_material_attachments
    AFTER INSERT OR UPDATE OR DELETE ON attachments
    FOR EACH ROW EXECUTE FUNCTION update_material_attachments();

-- 9. 현재 상태 확인
SELECT 
    'materials' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN has_attachments = true THEN 1 END) as with_attachments
FROM materials
UNION ALL
SELECT 
    'attachments' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN source_type = 'lecture_materials' THEN 1 END) as material_attachments
FROM attachments;
