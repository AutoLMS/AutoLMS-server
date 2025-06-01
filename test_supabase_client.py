#!/usr/bin/env python3
"""Supabase 클라이언트 연결 테스트"""

import asyncio
from supabase import create_client, Client
import os

def test_supabase_client():
    """Supabase 클라이언트 테스트"""
    
    # 환경변수 설정
    SUPABASE_URL = "https://uukkvisuqhopdraeaawz.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV1a2t2aXN1cWhvcGRyYWVhYXd6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDg2OTg5NDIsImV4cCI6MjA2NDI3NDk0Mn0.sKEkKBv8miYH4-UOwHQ75VpGDsvR7uSw_C0Vm8Uz2wA"
    
    try:
        print(f"Supabase 클라이언트 연결 시도: {SUPABASE_URL}")
        
        # Supabase 클라이언트 생성
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        print("클라이언트 생성 성공")
        
        # 테이블 목록 확인
        try:
            # 간단한 쿼리 테스트 - 테이블 존재 확인
            result = supabase.table('courses').select('*').limit(1).execute()
            print(f"courses 테이블 접근 성공: {len(result.data)}개 행")
        except Exception as e:
            print(f"courses 테이블 접근 실패: {e}")
            
        try:
            # 사용자 테이블 확인
            result = supabase.table('users').select('*').limit(1).execute()
            print(f"users 테이블 접근 성공: {len(result.data)}개 행")
        except Exception as e:
            print(f"users 테이블 접근 실패: {e}")
        
        # RPC 함수 테스트 (있다면)
        try:
            result = supabase.rpc('ping').execute()
            print(f"RPC 호출 성공: {result.data}")
        except Exception as e:
            print(f"RPC 호출 실패 (정상): {e}")
            
        print("Supabase 클라이언트 테스트 완료")
        
    except Exception as e:
        print(f"Supabase 클라이언트 연결 실패: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_supabase_client()