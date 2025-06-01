# AutoLMS-refactor

서울과학기술대학교 e-Class 학습관리시스템의 공지사항, 강의자료, 과제 등을 자동으로 수집하고 관리하는 API 서버입니다. 이 프로젝트는 기존 AutoLMS의 리팩토링 버전입니다.

## 주요 기능

- 강의 목록 자동 수집
- 공지사항, 강의자료, 과제 데이터 크롤링
- 첨부파일 자동 다운로드 및 Supabase 스토리지 업로드
- RestAPI를 통한 데이터 접근
- 백그라운드 크롤링 작업 지원
- Supabase Auth를 이용한 사용자 인증

## 기술 스택

- **백엔드**: FastAPI, Python 3.9+
- **데이터베이스**: PostgreSQL (SQLAlchemy ORM)
- **파일 스토리지**: Supabase Storage
- **인증**: Supabase Auth
- **비동기 처리**: asyncio, httpx
- **HTML 파싱**: BeautifulSoup4

## 설치 방법

1. 저장소 클론
```bash
git clone https://github.com/yourusername/AutoLMS-refactor.git
cd AutoLMS-refactor
```

2. 가상환경 생성 및 활성화
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

3. 의존성 설치
```bash
pip install -r requirements.txt
```

4. 환경 변수 설정 (.env 파일 편집)
```
# 서버 설정
HOST=0.0.0.0
PORT=8000
RELOAD=true

# 데이터베이스 설정
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=autolms

# Supabase 설정
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_BUCKET_NAME=autolms-file

# E-Class 설정
ECLASS_USERNAME=your_eclass_username
ECLASS_PASSWORD=your_eclass_password
```

5. 데이터베이스 마이그레이션
```bash
alembic upgrade head
```

## 실행 방법

```bash
# 개발 모드 실행
uvicorn main:app --reload

# 또는
python main.py
```

서버 실행 후 http://localhost:8000/docs 에서 Swagger UI를 통해 API 문서를 확인할 수 있습니다.

## API 엔드포인트

기본 API URL: `/api/v1`

### 인증

- `POST /auth/register` - 사용자 등록
- `POST /auth/login` - 로그인 및 토큰 발급
- `POST /auth/logout` - 로그아웃

### 강의

- `GET /courses` - 모든 강의 목록 조회
- `GET /courses/{course_id}` - 특정 강의 정보 조회
- `POST /courses/refresh` - 강의 목록 새로고침

### 공지사항

- `GET /courses/{course_id}/notices` - 공지사항 목록 조회
- `GET /courses/{course_id}/notices/{notice_id}` - 특정 공지사항 상세 조회
- `POST /courses/{course_id}/notices/refresh` - 공지사항 새로고침

### 강의자료

- `GET /courses/{course_id}/materials` - 강의자료 목록 조회
- `GET /courses/{course_id}/materials/{material_id}` - 특정 강의자료 상세 조회
- `POST /courses/{course_id}/materials/refresh` - 강의자료 새로고침

### 과제

- `GET /courses/{course_id}/assignments` - 과제 목록 조회
- `GET /courses/{course_id}/assignments/{assignment_id}` - 특정 과제 상세 조회
- `POST /courses/{course_id}/assignments/refresh` - 과제 새로고침

### 첨부파일

- `GET /attachments/{attachment_id}` - 첨부파일 메타데이터 조회
- `GET /attachments/{attachment_id}/download` - 첨부파일 다운로드
- `GET /attachments/by-source/{source_type}/{source_id}` - 소스별 첨부파일 조회
- `GET /attachments/search` - 첨부파일 검색

### 크롤링

- `POST /crawl/all` - 모든 과목 크롤링 시작
- `POST /crawl/course/{course_id}` - 특정 과목 크롤링 시작
- `GET /crawl/status/{task_id}` - 크롤링 작업 상태 조회
- `POST /crawl/cancel/{task_id}` - 크롤링 작업 취소

## 프로젝트 구조

```
AutoLMS-R/
├── app/                 # 메인 애플리케이션
│   ├── api/            # API 엔드포인트
│   ├── core/           # 핵심 설정
│   ├── db/             # 데이터베이스 관련
│   ├── models/         # 데이터 모델
│   ├── schemas/        # Pydantic 스키마
│   └── services/       # 비즈니스 로직
├── tests/              # 테스트 파일들
├── scripts/            # 설정 및 유틸리티 스크립트
├── sql/                # SQL 스크립트
├── api-docs/           # API 문서 (Postman 컬렉션)
├── test_data/          # 테스트 데이터
└── alembic/            # 데이터베이스 마이그레이션
```

## 개발자 문서

- **API 문서**: `/docs` 엔드포인트 또는 `api-docs/` 폴더의 Postman 컬렉션
- **테스트**: `tests/README.md` 참조
- **스크립트**: `scripts/README.md` 참조
- **SQL**: `sql/README.md` 참조

## 라이선스

MIT
