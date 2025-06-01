#!/usr/bin/env python3
"""Courses 테이블 확인"""

from app.core.supabase_client import get_supabase_client

def check_courses():
    """Courses 테이블 확인"""
    supabase = get_supabase_client()
    
    try:
        result = supabase.table('courses').select("*").limit(5).execute()
        print(f"✅ Courses 테이블 데이터: {len(result.data)}개")
        
        if result.data:
            for course in result.data:
                print(f"  - {course.get('course_name', 'No name')} ({course.get('course_id', 'No ID')})")
        else:
            print("📝 Courses 테이블이 비어있습니다.")
            
    except Exception as e:
        print(f"❌ Courses 테이블 조회 오류: {e}")

if __name__ == "__main__":
    check_courses()
