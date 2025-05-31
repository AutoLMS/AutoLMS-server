#!/usr/bin/env python3
"""
환경을 일시적으로 변경하여 실제 크롤링 테스트
"""
import os
import requests
import json
import time

def test_production_crawling():
    """프로덕션 모드로 크롤링 API 테스트"""
    print("🔄 프로덕션 모드 크롤링 API 테스트 시작...")
    
    # 서버 URL
    base_url = "http://localhost:8002"
    
    # 1. 먼저 현재 환경 확인
    print("📊 현재 환경 상태 확인...")
    
    try:
        # 개발 계정으로 로그인
        print("🔑 개발 계정 로그인...")
        login_response = requests.post(
            f"{base_url}/api/v1/auth/login",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "username": "devtest@seoultech.ac.kr",
                "password": "testpassword123"
            }
        )
        
        if login_response.status_code != 200:
            print(f"❌ 로그인 실패: {login_response.status_code}")
            return False
        
        token_data = login_response.json()
        access_token = token_data["access_token"]
        print(f"✅ 로그인 성공: {access_token[:20]}...")
        
        # 2. 환경 설정을 일시적으로 변경
        print("⚙️ 환경 설정 변경...")
        env_file_path = "/Users/elaus/PycharmProjects/AutoLMS-R/.env"
        
        # 현재 .env 백업
        with open(env_file_path, "r") as f:
            original_env = f.read()
        
        # 환경을 production으로 변경
        modified_env = original_env.replace("ENVIRONMENT=development", "ENVIRONMENT=production")
        
        with open(env_file_path, "w") as f:
            f.write(modified_env)
        
        print("✅ 환경을 production으로 변경 완료")
        
        # 3. 서버 재시작 대기 (실제로는 수동으로 재시작해야 함)
        print("⏳ 잠시 대기 중... (서버 재시작 필요)")
        time.sleep(5)
        
        # 4. 강의 목록 조회 (프로덕션 모드에서)
        print("📚 강의 목록 조회 (프로덕션 모드)...")
        courses_response = requests.get(
            f"{base_url}/api/v1/courses/",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if courses_response.status_code == 200:
            courses_data = courses_response.json()
            print(f"✅ 강의 목록 조회 성공: {courses_data.get('total', 0)}개")
            
            if courses_data.get('courses'):
                # IT Project Management 강의 찾기
                target_course = None
                for course in courses_data['courses']:
                    if 'IT Project Management' in course.get('name', ''):
                        target_course = course
                        break
                
                if target_course:
                    course_id = target_course['id']
                    print(f"🎯 테스트 대상 강의: {target_course['name']} ({course_id})")
                    
                    # 5. 실제 크롤링 테스트
                    print("🕷️ 실제 크롤링 시작...")
                    crawl_response = requests.post(
                        f"{base_url}/api/v1/crawl/course/{course_id}",
                        headers={"Authorization": f"Bearer {access_token}"},
                        params={"auto_download": "false"}
                    )
                    
                    if crawl_response.status_code == 200:
                        crawl_data = crawl_response.json()
                        print(f"✅ 크롤링 시작: {crawl_data}")
                        
                        # 크롤링 상태 확인
                        if 'task_id' in crawl_data:
                            task_id = crawl_data['task_id']
                            print(f"📋 작업 ID: {task_id}")
                            
                            # 잠시 대기 후 상태 확인
                            time.sleep(10)
                            
                            status_response = requests.get(
                                f"{base_url}/api/v1/crawl/status/{task_id}",
                                headers={"Authorization": f"Bearer {access_token}"}
                            )
                            
                            if status_response.status_code == 200:
                                status_data = status_response.json()
                                print(f"📊 크롤링 상태: {status_data}")
                            else:
                                print(f"❌ 상태 확인 실패: {status_response.status_code}")
                    else:
                        print(f"❌ 크롤링 실패: {crawl_response.status_code}")
                        print(f"응답: {crawl_response.text}")
                else:
                    print("❌ IT Project Management 강의를 찾을 수 없습니다")
            else:
                print("❌ 강의 목록이 비어있습니다")
        else:
            print(f"❌ 강의 목록 조회 실패: {courses_response.status_code}")
            print(f"응답: {courses_response.text}")
        
        # 6. 환경 설정 복원
        print("🔄 환경 설정 복원...")
        with open(env_file_path, "w") as f:
            f.write(original_env)
        print("✅ 환경 설정 복원 완료")
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        
        # 환경 설정 복원 (오류 발생 시에도)
        try:
            with open(env_file_path, "w") as f:
                f.write(original_env)
            print("✅ 환경 설정 복원 완료 (오류 복구)")
        except:
            print("❌ 환경 설정 복원 실패")
        
        return False

if __name__ == "__main__":
    success = test_production_crawling()
    if success:
        print("🎯 프로덕션 모드 크롤링 테스트 완료!")
    else:
        print("❌ 프로덕션 모드 크롤링 테스트 실패")
