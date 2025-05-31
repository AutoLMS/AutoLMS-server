import asyncio
import sys
sys.path.append('/Users/elaus/PycharmProjects/AutoLMS-R')

from app.services.eclass_service import EclassService
from app.services.eclass_session import EclassSession  
from app.services.eclass_parser import EclassParser
from app.services.file_handler import FileHandler
from app.core.config import settings

async def test_eclass_crawling():
    try:
        print("🔍 eClass 크롤링 테스트 시작...")
        
        # 서비스 컴포넌트 초기화
        session = EclassSession()
        parser = EclassParser()
        file_handler = FileHandler()
        
        eclass_service = EclassService(
            session=session,
            parser=parser, 
            file_handler=file_handler
        )
        
        print(f"📧 로그인 계정: {settings.ECLASS_USERNAME}")
        
        # eClass 로그인
        login_success = await eclass_service.login(
            settings.ECLASS_USERNAME, 
            settings.ECLASS_PASSWORD
        )
        
        if not login_success:
            print("❌ eClass 로그인 실패")
            return False
            
        print("✅ eClass 로그인 성공!")
        
        # 강의 목록 조회 (데이터베이스 없이)
        courses = await eclass_service._crawl_courses()
        
        print(f"📚 발견된 강의 수: {len(courses)}")
        for i, course in enumerate(courses[:3], 1):  # 처음 3개만 출력
            print(f"  {i}. {course.get('name', 'N/A')} (ID: {course.get('id', 'N/A')})")
        
        # 첫 번째 강의의 상세 정보 크롤링
        if courses:
            first_course = courses[0]
            course_id = first_course.get('id')
            print(f"\n🔍 강의 '{first_course.get('name')}' 상세 크롤링...")
            
            # 강의자료 크롤링
            materials = await eclass_service._crawl_materials(course_id)
            print(f"📄 강의자료 수: {len(materials)}")
            
            # 공지사항 크롤링  
            notices = await eclass_service._crawl_notices(course_id)
            print(f"📢 공지사항 수: {len(notices)}")
            
            # 과제 크롤링
            assignments = await eclass_service._crawl_assignments(course_id)
            print(f"📝 과제 수: {len(assignments)}")
            
            return {
                "courses": courses,
                "materials": materials,
                "notices": notices, 
                "assignments": assignments
            }
        
        return {"courses": courses}
        
    except Exception as e:
        print(f"❌ 크롤링 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_eclass_crawling())
    if result:
        print("\n🎉 eClass 크롤링 테스트 성공!")
        print("✨ 이제 이 데이터를 API 응답에 사용할 수 있습니다!")
    else:
        print("\n❌ eClass 크롤링 테스트 실패")
