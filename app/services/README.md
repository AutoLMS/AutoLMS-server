# 서비스 계층 구조

이 디렉토리는 AutoLMS의 서비스 계층을 포함합니다. 서비스 계층은 애플리케이션의 비즈니스 로직을 구현합니다.

## 디렉토리 구조

```
app/services/
├── parsers/           # 파싱 관련 서비스
│   ├── content_parser.py     # 콘텐츠 파서 기본 클래스
│   ├── course_parser.py      # 강의 파서
│   ├── notice_parser.py      # 공지사항 파서
│   ├── material_parser.py    # 강의자료 파서
│   ├── assignment_parser.py  # 과제 파서
│   └── syllabus_parser.py    # 강의계획서 파서
│
├── core/              # 핵심 서비스
│   ├── session_service.py    # 세션 관리 서비스
│   └── eclass_session.py     # 이클래스 세션 클래스
│
├── content/           # 콘텐츠 관련 서비스
│   ├── course_service.py     # 강의 서비스
│   ├── notice_service.py     # 공지사항 서비스
│   ├── material_service.py   # 강의자료 서비스
│   ├── assignment_service.py # 과제 서비스
│   └── syllabus_service.py   # 강의계획서 서비스
│
├── storage/           # 저장소 관련 서비스
│   └── storage_service.py    # 파일 저장소 서비스
│
├── sync/              # 동기화 관련 서비스
│   └── crawl_service.py      # 크롤링 작업 관리 서비스
│
├── base_service.py    # 기본 서비스 인터페이스
└── content_service.py # 콘텐츠 서비스 추상 클래스
```

## 리팩토링 방향

1. 기존의 단일 EclassService를 작은 전문화된 서비스로 분리
2. 각 서비스는 자신의 도메인에만 집중하고 다른 서비스와 협력
3. 파서는 서비스에 주입되어 사용됨 (의존성 주입)
4. 서비스 간 의존성을 명확하게 정의
