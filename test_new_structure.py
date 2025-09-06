#!/usr/bin/env python3
import os
import requests
import json
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

def test_new_table_structure():
    print("🔍 Testing new table structure...")
    
    try:
        # 1. Check courses table (새로운 구조)
        print("\n1. Checking courses table structure:")
        courses = supabase.table('courses').select('*').limit(3).execute()
        print(f"   Courses count: {len(courses.data) if courses.data else 0}")
        if courses.data:
            print(f"   Sample course: {courses.data[0]}")
        
        # 2. Check user_courses table
        print("\n2. Checking user_courses table:")
        user_courses = supabase.table('user_courses').select('*').limit(3).execute()
        print(f"   User-courses mappings count: {len(user_courses.data) if user_courses.data else 0}")
        if user_courses.data:
            print(f"   Sample mapping: {user_courses.data[0]}")
        
        # 3. Test join query
        print("\n3. Testing join query:")
        joined_data = supabase.table('user_courses')\
            .select("""
                *,
                courses (
                    course_id,
                    course_name,
                    instructor
                )
            """)\
            .limit(2)\
            .execute()
        print(f"   Joined data count: {len(joined_data.data) if joined_data.data else 0}")
        if joined_data.data:
            print(f"   Sample joined: {joined_data.data[0]}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def test_api_login_and_courses():
    print("\n🧪 Testing API login and courses...")
    
    base_url = "http://localhost:8000/api/v1"
    
    try:
        # 1. Login
        print("1. Testing login...")
        login_data = {
            "eclass_username": os.getenv("ECLASS_USERNAME", "testuser"),
            "eclass_password": os.getenv("ECLASS_PASSWORD", "testpass")
        }
        
        response = requests.post(f"{base_url}/auth/login", json=login_data)
        print(f"   Login status: {response.status_code}")
        
        if response.status_code == 200:
            login_result = response.json()
            token = login_result.get("access_token")
            print(f"   Token obtained: {token[:50]}..." if token else "   No token")
            
            # 2. Test /auth/me
            print("\n2. Testing /auth/me...")
            headers = {"Authorization": f"Bearer {token}"}
            me_response = requests.get(f"{base_url}/auth/me", headers=headers)
            print(f"   /auth/me status: {me_response.status_code}")
            if me_response.status_code == 200:
                user_info = me_response.json()
                print(f"   User ID: {user_info.get('id')}")
                print(f"   Username: {user_info.get('username')}")
            
            # 3. Test courses endpoint
            print("\n3. Testing /courses endpoint...")
            courses_response = requests.get(f"{base_url}/courses/?skip=0&limit=100", headers=headers)
            print(f"   Courses status: {courses_response.status_code}")
            
            if courses_response.status_code == 200:
                courses_result = courses_response.json()
                courses_list = courses_result.get("courses", [])
                print(f"   Courses count: {len(courses_list)}")
                print(f"   Total: {courses_result.get('total', 0)}")
                
                if courses_list:
                    print(f"   First course: {courses_list[0].get('course_name', 'Unknown')}")
                    print(f"   Course ID: {courses_list[0].get('course_id', 'Unknown')}")
                else:
                    print("   ❌ No courses returned")
            else:
                print(f"   ❌ Courses request failed: {courses_response.text}")
        else:
            print(f"   ❌ Login failed: {response.text}")
            
    except Exception as e:
        print(f"❌ API Test Error: {e}")

if __name__ == "__main__":
    test_new_table_structure()
    test_api_login_and_courses()