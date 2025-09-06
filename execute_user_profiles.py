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

# Create client with service key for admin operations
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Read the SQL file
with open('create_user_profiles_table.sql', 'r') as f:
    sql_content = f.read()

# Execute the SQL
try:
    print("🚀 Creating user_profiles table...")
    
    # Split SQL commands by semicolon and execute each one
    sql_commands = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip()]
    
    for i, command in enumerate(sql_commands, 1):
        if command:
            print(f"Executing command {i}...")
            result = supabase.rpc('exec_sql', {'sql': command}).execute()
            if result.data:
                print(f"✅ Command {i} executed successfully")
    
    print("✅ user_profiles table created successfully with RLS policies!")
    
except Exception as e:
    print(f"❌ Error creating user_profiles table: {e}")
    print("Trying alternative approach...")
    
    # Alternative approach using direct SQL execution
    try:
        # Create table first
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS user_profiles (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE NOT NULL,
            autolms_id VARCHAR(255) UNIQUE NOT NULL,
            eclass_username VARCHAR(100) NOT NULL,
            eclass_session_token TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        result = supabase.rpc('exec_sql', {'sql': create_table_sql}).execute()
        print("✅ Table creation completed")
        
    except Exception as e2:
        print(f"❌ Alternative approach also failed: {e2}")
        print("Please create the table manually in Supabase Dashboard")