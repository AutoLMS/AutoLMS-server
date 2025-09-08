#!/usr/bin/env python3

"""
특정 강의의 강의자료 가져오기 테스트
"""

import asyncio
import json
from app.services.auth_service import AuthService
from app.services.eclass_service import EclassService

async def test_course_materials():
    """특정 강의의 강의자료 테스트"""
    try:
        print("🔐 인증 시작...")
        
        # 기존 로그인된 사용자 ID 사용
        user_id = "7eb9befa-2833-456b-b857-08d71b226fe5"
        
        # AuthService로 자격증명 가져오기
        auth_service = AuthService()
        eclass_credentials = await auth_service.get_user_eclass_credentials(user_id)
        print(f"✅ 자격증명 조회 성공: {eclass_credentials['eclass_username']}")
        
        # eClass 서비스 로그인
        eclass_service = EclassService()
        login_success = await eclass_service.login(
            eclass_credentials["eclass_username"], 
            eclass_credentials["eclass_password"]
        )
        
        if not login_success:
            print("❌ eClass 로그인 실패")
            return False
        
        print("✅ eClass 로그인 성공")
        
        # 강의자료 조회 테스트
        course_id = "A2025310902931001"
        print(f"\n📚 강의자료 조회 시작: {course_id}")
        print("=" * 80)
        
        # 1. 크롤링부터 시작
        print("1️⃣ 강의 크롤링 시작...")
        crawl_result = await eclass_service.crawl_course(user_id, course_id, auto_download=False, is_jwt_user=True)
        task_id = crawl_result.get("task_id")
        
        if task_id:
            print(f"✅ 크롤링 작업 시작됨: {task_id}")
            
            # 완료 대기
            print("⏳ 크롤링 완료 대기...")
            for i in range(15):  # 최대 30초 대기
                await asyncio.sleep(2)
                status_result = await eclass_service.get_task_status(task_id)
                if status_result.get("status") == "completed":
                    print("✅ 크롤링 완료!")
                    break
                elif i % 5 == 0:
                    print(f"   진행 중... ({i*2}초 경과)")
        
        # 2. 강의자료 조회
        print(f"\n2️⃣ 강의자료 조회...")
        materials = await eclass_service.get_materials(user_id, course_id, is_jwt_user=True)
        
        print(f"📊 강의자료 조회 결과:")
        print(f"   - 총 개수: {len(materials)}")
        
        if materials:
            print(f"✅ 강의자료 데이터 확인됨!")
            
            for i, material in enumerate(materials[:3], 1):  # 처음 3개만 표시
                print(f"\n📄 강의자료 #{i}:")
                print(f"   - 제목: {material.get('title', 'N/A')}")
                print(f"   - 작성자: {material.get('author', 'N/A')}")
                print(f"   - 작성일: {material.get('date', 'N/A')}")
                print(f"   - 조회수: {material.get('views', 'N/A')}")
                print(f"   - 내용: {str(material.get('content', 'N/A'))[:100]}...")
                print(f"   - 첨부파일: {len(material.get('attachments', []))}개")
                
                if material.get('attachments'):
                    print(f"     첨부파일 목록:")
                    for j, attachment in enumerate(material['attachments'][:2], 1):  # 처음 2개만
                        print(f"       {j}. {attachment.get('file_name', 'Unknown')}")
            
            if len(materials) > 3:
                print(f"\n... 및 {len(materials) - 3}개 더")
        else:
            print("⚠️ 강의자료가 없습니다")
        
        # 3. API 응답 형태 시뮬레이션
        print(f"\n3️⃣ API 응답 형태 시뮬레이션:")
        api_response = {
            "materials": materials,
            "total": len(materials),
            "course_id": course_id
        }
        
        print(f"응답 구조:")
        print(f"   - materials: {type(api_response['materials'])} ({len(api_response['materials'])}개)")
        print(f"   - total: {api_response['total']}")
        print(f"   - course_id: {api_response['course_id']}")
        
        # JSON 직렬화 테스트
        try:
            json_str = json.dumps(api_response, indent=2, ensure_ascii=False, default=str)
            print(f"✅ JSON 직렬화 성공 (길이: {len(json_str)} 문자)")
            
            # 샘플 출력
            if len(json_str) > 1000:
                print(f"📄 JSON 샘플 (처음 1000자):")
                print(json_str[:1000])
                print("...")
            else:
                print(f"📄 전체 JSON:")
                print(json_str)
                
        except Exception as json_error:
            print(f"❌ JSON 직렬화 실패: {json_error}")
        
        return len(materials) > 0
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    result = asyncio.run(test_course_materials())
    print("\n" + "="*80)
    if result:
        print("✅ 강의자료 테스트 성공! 스웨거 UI에서도 정상 작동할 것입니다.")
    else:
        print("❌ 강의자료 테스트 실패")