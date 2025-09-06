#!/usr/bin/env python3
import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

def debug_course_data():
    print("🔍 Debugging course data...")
    
    # 1. 현재 로그인한 사용자 ID
    current_user_id = "501d59b4-6bf4-4155-95db-7b736743c7d3"
    print(f"현재 사용자 ID: {current_user_id}")
    
    # 2. 현재 사용자의 강의 확인
    user_courses = supabase.table('courses').select('*').eq('user_id', current_user_id).execute()
    print(f"\n현재 사용자의 강의 수: {len(user_courses.data) if user_courses.data else 0}")
    
    # 3. 모든 강의 확인
    all_courses = supabase.table('courses').select('user_id, course_id, course_name').execute()
    print(f"전체 강의 수: {len(all_courses.data) if all_courses.data else 0}")
    
    # 4. user_id별 그룹화
    user_groups = {}
    if all_courses.data:
        for course in all_courses.data:
            user_id = course['user_id']
            if user_id not in user_groups:
                user_groups[user_id] = []
            user_groups[user_id].append(course['course_id'])
    
    print(f"\nuser_id별 강의 분포:")
    for user_id, course_ids in user_groups.items():
        print(f"  {user_id}: {len(course_ids)}개 강의")
        if user_id == current_user_id:
            print(f"    --> 현재 사용자 (강의들: {course_ids[:3]}...)")
    
    # 5. 중복되는 course_id들 찾기
    course_id_counts = {}
    if all_courses.data:
        for course in all_courses.data:
            course_id = course['course_id']
            if course_id not in course_id_counts:
                course_id_counts[course_id] = []
            course_id_counts[course_id].append(course['user_id'])
    
    duplicates = {k: v for k, v in course_id_counts.items() if len(v) > 1}
    print(f"\n중복 course_id 수: {len(duplicates)}")
    if duplicates:
        for course_id, user_ids in list(duplicates.items())[:3]:
            print(f"  {course_id}: {user_ids}")

if __name__ == "__main__":
    debug_course_data()