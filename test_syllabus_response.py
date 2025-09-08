#!/usr/bin/env python3

"""
강의계획서 응답 데이터 구조 확인 테스트
"""

import asyncio
import json
from app.services.auth_service import AuthService
from app.services.eclass_service import EclassService

async def test_syllabus_response():
    """강의계획서 API 응답 데이터 구조 확인"""
    try:
        print("🔐 인증 시작...")
        
        # 기존 로그인된 사용자 ID 사용 (메타데이터가 업데이트된 사용자)
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
        
        # 강의계획서 조회
        course_id = "A2025310911441009"
        print(f"\n📋 강의계획서 조회 시작: {course_id}")
        
        syllabus = await eclass_service.get_syllabus(user_id, course_id)
        
        print("=" * 60)
        print("📊 강의계획서 응답 데이터 분석")
        print("=" * 60)
        
        print(f"응답 타입: {type(syllabus)}")
        print(f"응답이 비어있음: {not syllabus}")
        
        if isinstance(syllabus, dict):
            print(f"키 개수: {len(syllabus)}")
            print(f"키 목록: {list(syllabus.keys())}")
            
            for key, value in syllabus.items():
                if isinstance(value, dict):
                    print(f"\n🔸 {key} (딕셔너리, {len(value)}개 항목):")
                    if value:
                        for sub_key, sub_value in value.items():
                            print(f"   - {sub_key}: {str(sub_value)[:100]}...")
                    else:
                        print("   (비어있음)")
                elif isinstance(value, list):
                    print(f"\n🔸 {key} (리스트, {len(value)}개 항목):")
                    if value:
                        for i, item in enumerate(value[:3]):  # 처음 3개만
                            print(f"   [{i}]: {str(item)[:100]}...")
                        if len(value) > 3:
                            print(f"   ... 및 {len(value) - 3}개 더")
                    else:
                        print("   (비어있음)")
                else:
                    print(f"\n🔸 {key}: {str(value)[:200]}...")
        
        print("\n" + "=" * 60)
        print("📄 JSON 형태 (처음 1000자)")
        print("=" * 60)
        
        json_str = json.dumps(syllabus, indent=2, ensure_ascii=False, default=str)
        print(json_str[:1000])
        if len(json_str) > 1000:
            print("...")
            print(f"(총 {len(json_str)}자)")
        
        print("\n" + "=" * 60)
        
        # API 응답 형태로 포장
        api_response = {
            "course_id": course_id,
            "syllabus": syllabus,
            "status": "success"
        }
        
        print("🔄 API 응답 형태 시뮬레이션:")
        print(f"응답 타입: {type(api_response)}")
        print(f"키 목록: {list(api_response.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    result = asyncio.run(test_syllabus_response())
    print("\n" + "="*60)
    if result:
        print("✅ 강의계획서 응답 데이터 분석 완료!")
    else:
        print("❌ 강의계획서 응답 데이터 분석 실패")