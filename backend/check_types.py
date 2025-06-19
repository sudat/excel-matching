#!/usr/bin/env python3
"""
Check Supabase Python client type definitions
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import inspect

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

def check_select_signature():
    """Check the select method signature and types"""
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        print("ERROR: Supabase configuration not found")
        return
    
    # Create Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    
    # Get the table object
    table_obj = supabase.table('business_requests')
    
    # Check the select method signature
    print("Select method signature:")
    sig = inspect.signature(table_obj.select)
    print(f"Signature: {sig}")
    
    # Print parameter details
    for param_name, param in sig.parameters.items():
        print(f"  {param_name}: {param.annotation} (default: {param.default})")
    
    # Let's also check the actual module imports and types
    print("\nModule information:")
    print(f"Table object type: {type(table_obj)}")
    print(f"Select method type: {type(table_obj.select)}")
    
    # Try to import CountMethod type if available
    try:
        from postgrest import CountMethod
        print(f"\nCountMethod type found: {CountMethod}")
        print(f"CountMethod values: {list(CountMethod) if hasattr(CountMethod, '__iter__') else 'Not iterable'}")
    except ImportError as e:
        print(f"\nCountMethod import failed: {e}")
    
    # Try to import from different locations
    try:
        from postgrest.constants import CountMethod as ConstCountMethod
        print(f"CountMethod from constants: {ConstCountMethod}")
    except ImportError:
        print("CountMethod not found in postgrest.constants")
    
    # Check postgrest version and types
    try:
        import postgrest
        print(f"\nPostgrest version: {getattr(postgrest, '__version__', 'Unknown')}")
        
        # Check what's available in postgrest module
        postgrest_attrs = [attr for attr in dir(postgrest) if not attr.startswith('_')]
        print(f"Postgrest public attributes: {postgrest_attrs}")
        
    except ImportError:
        print("Postgrest module not available")

if __name__ == "__main__":
    check_select_signature()