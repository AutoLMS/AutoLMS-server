-- Supabase SQL 업데이트 스크립트

-- courses 테이블 생성
CREATE TABLE IF NOT EXISTS public.courses (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    code TEXT,
    time TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- RLS 정책 설정
ALTER TABLE public.courses ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Courses are viewable by authenticated users" ON public.courses
    FOR SELECT USING (auth.uid()::text = user_id);
CREATE POLICY "Users can insert their own courses" ON public.courses
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);
CREATE POLICY "Users can update own courses" ON public.courses
    FOR UPDATE USING (auth.uid()::text = user_id);

-- assignments 테이블 생성
CREATE TABLE IF NOT EXISTS public.assignments (
    id SERIAL PRIMARY KEY,
    article_id TEXT NOT NULL,
    course_id TEXT NOT NULL REFERENCES public.courses(id),
    title TEXT NOT NULL,
    content TEXT,
    due_date TEXT,
    status TEXT,
    submission_status TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- RLS 정책 설정
ALTER TABLE public.assignments ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Assignments are viewable by course owners" ON public.assignments
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.courses 
            WHERE courses.id = assignments.course_id 
            AND courses.user_id = auth.uid()::text
        )
    );
CREATE POLICY "Users can insert assignments for their courses" ON public.assignments
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.courses 
            WHERE courses.id = assignments.course_id 
            AND courses.user_id = auth.uid()::text
        )
    );
CREATE POLICY "Users can update assignments for their courses" ON public.assignments
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM public.courses 
            WHERE courses.id = assignments.course_id 
            AND courses.user_id = auth.uid()::text
        )
    );

-- attachments 테이블 생성
CREATE TABLE IF NOT EXISTS public.attachments (
    id SERIAL PRIMARY KEY,
    course_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_size BIGINT,
    content_type TEXT,
    storage_path TEXT NOT NULL,
    original_url TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- RLS 정책 설정
ALTER TABLE public.attachments ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Attachments are viewable by course owners" ON public.attachments
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.courses 
            WHERE courses.id = attachments.course_id 
            AND courses.user_id = auth.uid()::text
        )
    );
CREATE POLICY "Users can insert attachments for their courses" ON public.attachments
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.courses 
            WHERE courses.id = attachments.course_id 
            AND courses.user_id = auth.uid()::text
        )
    );
CREATE POLICY "Users can update attachments for their courses" ON public.attachments
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM public.courses 
            WHERE courses.id = attachments.course_id 
            AND courses.user_id = auth.uid()::text
        )
    );

-- materials 테이블 생성
CREATE TABLE IF NOT EXISTS public.materials (
    id SERIAL PRIMARY KEY,
    article_id TEXT NOT NULL,
    course_id TEXT NOT NULL REFERENCES public.courses(id),
    title TEXT NOT NULL,
    content TEXT,
    author TEXT,
    date TEXT,
    views INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- RLS 정책 설정
ALTER TABLE public.materials ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Materials are viewable by course owners" ON public.materials
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.courses 
            WHERE courses.id = materials.course_id 
            AND courses.user_id = auth.uid()::text
        )
    );
CREATE POLICY "Users can insert materials for their courses" ON public.materials
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.courses 
            WHERE courses.id = materials.course_id 
            AND courses.user_id = auth.uid()::text
        )
    );
CREATE POLICY "Users can update materials for their courses" ON public.materials
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM public.courses 
            WHERE courses.id = materials.course_id 
            AND courses.user_id = auth.uid()::text
        )
    );

-- notices 테이블 생성
CREATE TABLE IF NOT EXISTS public.notices (
    id SERIAL PRIMARY KEY,
    article_id TEXT NOT NULL,
    course_id TEXT NOT NULL REFERENCES public.courses(id),
    title TEXT NOT NULL,
    content TEXT,
    author TEXT,
    date TEXT,
    views INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- RLS 정책 설정
ALTER TABLE public.notices ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Notices are viewable by course owners" ON public.notices
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.courses 
            WHERE courses.id = notices.course_id 
            AND courses.user_id = auth.uid()::text
        )
    );
CREATE POLICY "Users can insert notices for their courses" ON public.notices
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.courses 
            WHERE courses.id = notices.course_id 
            AND courses.user_id = auth.uid()::text
        )
    );
CREATE POLICY "Users can update notices for their courses" ON public.notices
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM public.courses 
            WHERE courses.id = notices.course_id 
            AND courses.user_id = auth.uid()::text
        )
    );

-- syllabus 테이블 생성
CREATE TABLE IF NOT EXISTS public.syllabus (
    id SERIAL PRIMARY KEY,
    course_id TEXT NOT NULL REFERENCES public.courses(id) UNIQUE,
    year_semester TEXT,
    course_type TEXT,
    professor_name TEXT,
    office_hours TEXT,
    homepage TEXT,
    course_overview TEXT,
    objectives TEXT,
    textbooks TEXT,
    equipment TEXT,
    evaluation_method TEXT,
    weekly_plans JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- RLS 정책 설정
ALTER TABLE public.syllabus ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Syllabus are viewable by course owners" ON public.syllabus
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.courses 
            WHERE courses.id = syllabus.course_id 
            AND courses.user_id = auth.uid()::text
        )
    );
CREATE POLICY "Users can insert syllabus for their courses" ON public.syllabus
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.courses 
            WHERE courses.id = syllabus.course_id 
            AND courses.user_id = auth.uid()::text
        )
    );
CREATE POLICY "Users can update syllabus for their courses" ON public.syllabus
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM public.courses 
            WHERE courses.id = syllabus.course_id 
            AND courses.user_id = auth.uid()::text
        )
    );

-- 스토리지 버킷 생성 (이미 존재하지 않는 경우)
-- 이 부분은 Supabase 대시보드에서 직접 설정하는 것이 좋습니다.
-- 파일 저장을 위한 storage 버킷
-- INSERT INTO storage.buckets (id, name, public) VALUES ('attachments', 'attachments', false)
-- ON CONFLICT (id) DO NOTHING;

-- 스토리지 정책
-- 이 부분도 Supabase 대시보드에서 직접 설정하는 것이 좋습니다.
