# API Documentation

이 폴더는 API 테스트 및 문서화를 위한 Postman 컬렉션들을 포함합니다.

## 파일 설명

- `AutoLMS-R_Final_API_Collection.postman_collection.json` - 최종 API 컬렉션 (권장)
- `AutoLMS-R_Working_API_Collection.postman_collection.json` - 작업 중인 API 컬렉션
- `AutoLMS-R_Updated_API_Collection.postman_collection.json` - 업데이트된 API 컬렉션
- `AutoLMS-R_API_Collection.postman_collection.json` - 초기 API 컬렉션

## 사용법

1. Postman 실행
2. Import 버튼 클릭
3. `AutoLMS-R_Final_API_Collection.postman_collection.json` 파일 선택
4. 환경 변수 설정:
   - `base_url`: http://localhost:8000
   - `token`: Bearer 토큰 (로그인 후 획득)

## API 엔드포인트

- **인증**: `/api/v1/auth/*`
- **강의**: `/api/v1/courses/*`
- **크롤링**: `/api/v1/crawl/*`
- **첨부파일**: `/api/v1/attachments/*`

## 권장 사용 순서

1. 사용자 등록/로그인
2. 강의 목록 조회
3. 크롤링 작업 시작
4. 결과 확인