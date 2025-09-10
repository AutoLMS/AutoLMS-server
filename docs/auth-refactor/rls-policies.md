# Supabase RLS Policies for Course Material Access Control

## 🎯 목표
강의자료 공유를 위한 권한 기반 접근 제어 시스템 구현  
같은 강의를 듣는 사용자들이 해당 강의의 자료에만 접근할 수 있도록 제한

## 📊 현재 데이터 구조

### 주요 테이블
```sql
-- 사용자 테이블
users {
  id: uuid (primary key, auth.uid() 연동)
  eclass_username: string
  eclass_password: string (encrypted)
  created_at: timestamp
}

-- 강의 테이블  
courses {
  id: string (primary key, eclass course_id)
  name: string
  code: string
  semester: string
  created_at: timestamp
}

-- 사용자-강의 중간 테이블
user_courses {
  user_id: uuid (foreign key -> users.id)
  course_id: string (foreign key -> courses.id)
  created_at: timestamp
}

-- 강의 자료 테이블들
materials {
  id: uuid (primary key)
  course_id: string (foreign key -> courses.id)
  title: string
  content: text
  created_at: timestamp
}

notices {
  id: uuid (primary key) 
  course_id: string (foreign key -> courses.id)
  title: string
  content: text
  created_at: timestamp
}

assignments {
  id: uuid (primary key)
  course_id: string (foreign key -> courses.id)
  title: string
  content: text  
  due_date: timestamp
  created_at: timestamp
}
```

## 🔐 RLS 정책 설계

### 1. 사용자 테이블 정책
```sql
-- users 테이블: 본인 데이터만 조회 가능
CREATE POLICY "Users can view own profile" ON users
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON users  
  FOR UPDATE USING (auth.uid() = id);
```

### 2. 강의 테이블 정책
```sql
-- courses 테이블: 등록된 강의만 조회 가능
CREATE POLICY "Users can view enrolled courses" ON courses
  FOR SELECT USING (
    id IN (
      SELECT course_id FROM user_courses 
      WHERE user_id = auth.uid()
    )
  );
```

### 3. 사용자-강의 관계 테이블 정책
```sql
-- user_courses 테이블: 본인 수강 정보만 접근 가능
CREATE POLICY "Users can view own course enrollments" ON user_courses
  FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can manage own course enrollments" ON user_courses
  FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can remove own course enrollments" ON user_courses
  FOR DELETE USING (user_id = auth.uid());
```

### 4. 강의자료 테이블 정책
```sql
-- materials 테이블: 수강 중인 강의의 자료만 접근 가능
CREATE POLICY "Users can access materials from enrolled courses" ON materials
  FOR SELECT USING (
    course_id IN (
      SELECT course_id FROM user_courses
      WHERE user_id = auth.uid()
    )
  );

-- notices 테이블: 수강 중인 강의의 공지만 접근 가능  
CREATE POLICY "Users can access notices from enrolled courses" ON notices
  FOR SELECT USING (
    course_id IN (
      SELECT course_id FROM user_courses
      WHERE user_id = auth.uid()  
    )
  );

-- assignments 테이블: 수강 중인 강의의 과제만 접근 가능
CREATE POLICY "Users can access assignments from enrolled courses" ON assignments
  FOR SELECT USING (
    course_id IN (
      SELECT course_id FROM user_courses
      WHERE user_id = auth.uid()
    )
  );
```

## 🚀 RLS 정책 적용 스크립트

### Supabase SQL Editor에서 실행할 스크립트
```sql
-- 1. RLS 활성화
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE courses ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_courses ENABLE ROW LEVEL SECURITY;
ALTER TABLE materials ENABLE ROW LEVEL SECURITY;  
ALTER TABLE notices ENABLE ROW LEVEL SECURITY;
ALTER TABLE assignments ENABLE ROW LEVEL SECURITY;

-- 2. 사용자 프로필 정책
CREATE POLICY "users_select_own" ON users
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "users_update_own" ON users
  FOR UPDATE USING (auth.uid() = id);

-- 3. 강의 접근 정책
CREATE POLICY "courses_select_enrolled" ON courses
  FOR SELECT USING (
    id IN (
      SELECT course_id FROM user_courses 
      WHERE user_id = auth.uid()
    )
  );

-- 4. 수강 관리 정책  
CREATE POLICY "user_courses_select_own" ON user_courses
  FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "user_courses_insert_own" ON user_courses  
  FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "user_courses_delete_own" ON user_courses
  FOR DELETE USING (user_id = auth.uid());

-- 5. 강의자료 접근 정책
CREATE POLICY "materials_select_enrolled" ON materials
  FOR SELECT USING (
    course_id IN (
      SELECT course_id FROM user_courses
      WHERE user_id = auth.uid()
    )
  );

CREATE POLICY "notices_select_enrolled" ON notices  
  FOR SELECT USING (
    course_id IN (
      SELECT course_id FROM user_courses
      WHERE user_id = auth.uid()
    )
  );

CREATE POLICY "assignments_select_enrolled" ON assignments
  FOR SELECT USING (
    course_id IN (
      SELECT course_id FROM user_courses  
      WHERE user_id = auth.uid()
    )
  );
```

## 🧪 테스트 시나리오

### 1. 정상 접근 테스트
```sql
-- 사용자 A가 수강 중인 강의 CS101의 자료 조회 (성공해야 함)
SELECT * FROM materials WHERE course_id = 'CS101';
-- RLS가 자동으로 user_courses 관계 확인
```

### 2. 비정상 접근 테스트  
```sql
-- 사용자 A가 수강하지 않는 강의 CS201의 자료 조회 (실패해야 함)
SELECT * FROM materials WHERE course_id = 'CS201';
-- RLS가 접근 차단, 빈 결과 반환
```

### 3. 사용자별 데이터 분리 테스트
```sql
-- 사용자 A의 토큰으로 로그인 후
SELECT * FROM user_courses;  -- A의 수강 정보만 보임

-- 사용자 B의 토큰으로 로그인 후  
SELECT * FROM user_courses;  -- B의 수강 정보만 보임
```

## 📊 성능 고려사항

### 인덱스 최적화
```sql
-- user_courses 테이블 인덱스 (RLS 쿼리 최적화)
CREATE INDEX idx_user_courses_user_id ON user_courses(user_id);
CREATE INDEX idx_user_courses_course_id ON user_courses(course_id);
CREATE INDEX idx_user_courses_user_course ON user_courses(user_id, course_id);

-- 강의자료 테이블 인덱스
CREATE INDEX idx_materials_course_id ON materials(course_id);
CREATE INDEX idx_notices_course_id ON notices(course_id);  
CREATE INDEX idx_assignments_course_id ON assignments(course_id);
```

### RLS 성능 모니터링
- Supabase Dashboard에서 쿼리 성능 모니터링
- 느린 쿼리 식별 및 인덱스 추가 최적화
- 필요시 더 효율적인 RLS 정책으로 개선

## 🔄 향후 확장 가능성

### 관리자 권한 추가
```sql  
-- 관리자는 모든 데이터 접근 가능
CREATE POLICY "admin_full_access" ON materials
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM users 
      WHERE id = auth.uid() AND role = 'admin'
    )
  );
```

### 강의별 역할 관리
```sql
-- user_courses에 role 컬럼 추가 (student, ta, instructor)
ALTER TABLE user_courses ADD COLUMN role VARCHAR(20) DEFAULT 'student';

-- 역할별 권한 차등 적용
CREATE POLICY "instructors_can_modify_materials" ON materials
  FOR ALL USING (
    course_id IN (
      SELECT course_id FROM user_courses
      WHERE user_id = auth.uid() AND role IN ('instructor', 'ta')
    )  
  );
```

## ✅ 적용 체크리스트

- [ ] Supabase 프로젝트에서 RLS 정책 스크립트 실행
- [ ] 테스트 계정으로 접근 권한 검증  
- [ ] 성능 인덱스 추가
- [ ] 애플리케이션 코드에서 RLS 정책 동작 확인
- [ ] 로그 모니터링으로 비정상 접근 시도 확인