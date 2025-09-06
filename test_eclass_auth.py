#!/usr/bin/env python3
"""
Test eClass authentication endpoints
"""
import asyncio
import requests
import json
from app.core.config import settings

# Test credentials (you'll need to replace with real ones)
TEST_ECLASS_USERNAME = "22102482"  # from your environment
TEST_ECLASS_PASSWORD = settings.ECLASS_PASSWORD if hasattr(settings, 'ECLASS_PASSWORD') else "your_password"

BASE_URL = "http://localhost:8001/api/v1/auth"

def test_eclass_register():
    """Test eClass registration"""
    print("🔍 Testing eClass Registration...")
    
    url = f"{BASE_URL}/eclass/register"
    data = {
        "eclass_username": TEST_ECLASS_USERNAME,
        "eclass_password": TEST_ECLASS_PASSWORD
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Registration successful!")
            print(f"User ID: {result['user']['id']}")
            print(f"Username: {result['user']['username']}")
            print(f"eClass Username: {result['user']['eclass_username']}")
            return result['access_token']
        else:
            print(f"❌ Registration failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error during registration: {e}")
        return None

def test_eclass_login():
    """Test eClass login"""
    print("\n🔍 Testing eClass Login...")
    
    url = f"{BASE_URL}/eclass/login"
    data = {
        "eclass_username": TEST_ECLASS_USERNAME,
        "eclass_password": TEST_ECLASS_PASSWORD
    }
    
    try:
        response = requests.post(url, json=data, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Login successful!")
            print(f"Access Token: {result['access_token'][:50]}...")
            return result['access_token']
        else:
            print(f"❌ Login failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error during login: {e}")
        return None

def test_get_current_user(access_token):
    """Test getting current user info with JWT token"""
    print("\n🔍 Testing Get Current User...")
    
    url = f"{BASE_URL}/me"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ User info retrieved successfully!")
            print(f"User ID: {result.get('id')}")
            print(f"Username: {result.get('username')}")
            print(f"eClass Username: {result.get('eclass_username')}")
            return True
        else:
            print(f"❌ Failed to get user info: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting user info: {e}")
        return False

def main():
    print("🚀 Starting eClass Authentication Tests...")
    print(f"Base URL: {BASE_URL}")
    print(f"Test eClass Username: {TEST_ECLASS_USERNAME}")
    
    # Test 1: Registration (might fail if user already exists)
    access_token = test_eclass_register()
    
    # Test 2: Login (should work)
    if not access_token:
        access_token = test_eclass_login()
    
    # Test 3: Get current user info
    if access_token:
        test_get_current_user(access_token)
    else:
        print("❌ No access token available for user info test")
    
    print("\n🎯 Test completed!")

if __name__ == "__main__":
    main()