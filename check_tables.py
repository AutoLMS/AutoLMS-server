#!/usr/bin/env python3
import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ SUPABASE_URL or SUPABASE_SERVICE_KEY not found in environment")
    exit(1)

# Create client with service key
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

try:
    print("🔍 Checking existing tables...")
    
    # Check user_profiles table
    try:
        result = supabase.table('user_profiles').select('*').limit(1).execute()
        print("✅ user_profiles table exists")
        if result.data:
            print(f"   Found {len(result.data)} records")
        else:
            print("   Table is empty")
    except Exception as e:
        print(f"❌ user_profiles table does not exist: {e}")
    
    # Check courses table structure
    try:
        result = supabase.table('courses').select('*').limit(1).execute()
        print("✅ courses table exists")
        if result.data:
            print(f"   Sample record keys: {list(result.data[0].keys()) if result.data else 'No data'}")
        else:
            print("   Table is empty")
    except Exception as e:
        print(f"❌ courses table issue: {e}")
        
    # Check auth.users table
    try:
        # Use RPC to check auth.users since it's in auth schema
        result = supabase.rpc('get_current_user').execute()
        print("✅ Can access auth functions")
    except Exception as e:
        print(f"ℹ️  Auth access: {e}")
        
except Exception as e:
    print(f"❌ Error checking tables: {e}")