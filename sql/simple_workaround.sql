-- 가장 간단한 해결책: 필수 컬럼만 추가
-- course_id 타입 변경이 복잡하다면 이 방법을 먼저 시도하세요

-- 1. 단순히 누락된 컬럼만 추가
ALTER TABLE notices ADD COLUMN IF NOT EXISTS article_id TEXT;
ALTER TABLE materials ADD COLUMN IF NOT EXISTS article_id TEXT; 
ALTER TABLE assignments ADD COLUMN IF NOT EXISTS article_id TEXT;

-- 2. 추가 필드들 (선택사항)
ALTER TABLE notices ADD COLUMN IF NOT EXISTS author TEXT;
ALTER TABLE notices ADD COLUMN IF NOT EXISTS date TEXT;
ALTER TABLE notices ADD COLUMN IF NOT EXISTS views INTEGER DEFAULT 0;

ALTER TABLE materials ADD COLUMN IF NOT EXISTS author TEXT;
ALTER TABLE materials ADD COLUMN IF NOT EXISTS date TEXT;
ALTER TABLE materials ADD COLUMN IF NOT EXISTS views INTEGER DEFAULT 0;

-- 3. attachments 테이블 개선
ALTER TABLE attachments ADD COLUMN IF NOT EXISTS file_name TEXT;
ALTER TABLE attachments ADD COLUMN IF NOT EXISTS original_url TEXT;
ALTER TABLE attachments ADD COLUMN IF NOT EXISTS storage_path TEXT DEFAULT '';

-- 4. 확인
SELECT table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_name IN ('notices', 'materials', 'assignments', 'attachments')
  AND column_name IN ('article_id', 'author', 'date', 'views', 'file_name', 'original_url')
ORDER BY table_name, column_name;