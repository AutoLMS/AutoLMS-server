#!/usr/bin/env python3
"""courses 테이블의 updated_at 컬럼 확인 스크립트"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.supabase_client import get_supabase_client

def check_courses_schema():
    """courses 테이블 스키마 확인"""
    try:
        client = get_supabase_client()
        
        # 테이블 스키마 확인을 위한 더미 조회
        response = client.table('courses').select('*').limit(1).execute()
        
        print("✅ courses 테이블 조회 성공")
        print(f"데이터 개수: {len(response.data)}")
        
        if response.data:
            print("\n📋 테이블 컬럼 목록:")
            for key in response.data[0].keys():
                print(f"  - {key}")
                
            if 'updated_at' in response.data[0]:
                print("\n✅ updated_at 컬럼이 존재합니다!")
                print(f"   값: {response.data[0].get('updated_at')}")
            else:
                print("\n❌ updated_at 컬럼이 없습니다!")
        else:
            print("\n📝 테이블이 비어있습니다.")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        print(f"오류 타입: {type(e)}")

if __name__ == "__main__":
    check_courses_schema()