#!/usr/bin/env python3
"""
Supabase Python client count='exact' parameter test
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

def test_count_parameter():
    """Test count='exact' parameter functionality"""
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        print("ERROR: Supabase configuration not found")
        return
    
    # Create Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    
    try:
        print("Testing count='exact' parameter...")
        
        # Test 1: Basic count query (the documented example)
        print("\n1. Testing basic count query:")
        print("Code: supabase.table('business_requests').select('*', count='exact').execute()")
        
        response = supabase.table('business_requests').select('*', count='exact').execute()
        print(f"Success: Got {len(response.data)} records")
        print(f"Count: {response.count}")
        
        # Test 2: Count without data
        print("\n2. Testing count without data:")
        print("Code: supabase.table('business_requests').select('*', count='exact').limit(0).execute()")
        
        response2 = supabase.table('business_requests').select('*', count='exact').limit(0).execute()
        print(f"Success: Got {len(response2.data)} records")
        print(f"Count: {response2.count}")
        
        # Test 3: Count with filtering
        print("\n3. Testing count with filtering:")
        print("Code: supabase.table('business_requests').select('*', count='exact').eq('status', 'pending').execute()")
        
        response3 = supabase.table('business_requests').select('*', count='exact').eq('status', 'pending').execute()
        print(f"Success: Got {len(response3.data)} records")
        print(f"Count: {response3.count}")
        
        print("\nAll tests passed successfully!")
        
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {str(e)}")
        print("This might indicate a version compatibility issue or incorrect usage.")
        
        # Let's also check the available count methods
        print("\nChecking available count methods...")
        try:
            # Try different variations
            alternatives = [
                ("count='estimated'", lambda: supabase.table('business_requests').select('*', count='estimated').execute()),
                ("count='planned'", lambda: supabase.table('business_requests').select('*', count='planned').execute()),
                ("count=None", lambda: supabase.table('business_requests').select('*', count=None).execute()),
            ]
            
            for name, func in alternatives:
                try:
                    result = func()
                    print(f"✓ {name} works - Count: {getattr(result, 'count', 'N/A')}")
                except Exception as alt_e:
                    print(f"✗ {name} failed: {str(alt_e)}")
                    
        except Exception as check_e:
            print(f"Error checking alternatives: {str(check_e)}")

if __name__ == "__main__":
    test_count_parameter()