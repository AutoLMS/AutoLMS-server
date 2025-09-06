#!/usr/bin/env python3
import os
import asyncio
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

async def debug_auth_issues():
    print("🔍 Debugging authentication issues...")
    
    try:
        # 1. Check user_profiles table
        print("\n1. Checking user_profiles table:")
        profiles = supabase.table('user_profiles').select('*').execute()
        print(f"   Found {len(profiles.data) if profiles.data else 0} user profiles")
        if profiles.data:
            for profile in profiles.data:
                print(f"   Profile: {profile}")
        
        # 2. Check auth.users table (via service key)
        print("\n2. Checking Supabase Auth users:")
        try:
            # This might not work directly, but let's try
            auth_users = supabase.auth.admin.list_users()
            print(f"   Found {len(auth_users) if auth_users else 0} auth users")
            if hasattr(auth_users, 'users') and auth_users.users:
                for user in auth_users.users[:3]:  # Show first 3
                    print(f"   User: ID={user.id}, Email={user.email}")
        except Exception as e:
            print(f"   Could not list auth users: {e}")
        
        # 3. Check courses table structure and permissions
        print("\n3. Checking courses table:")
        courses = supabase.table('courses').select('*').limit(3).execute()
        print(f"   Found {len(courses.data) if courses.data else 0} courses")
        if courses.data:
            print(f"   Sample course: {courses.data[0]}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_auth_issues())