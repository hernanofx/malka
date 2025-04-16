"""
Debug script to check environment variables and auth state
"""
import os
import json
import sys

def check_environment():
    """Check environment variables related to Google authentication"""
    print("=== Environment Variables Debug ===")
    
    # Check if GOOGLE_CREDENTIALS exists
    google_creds = os.environ.get('GOOGLE_CREDENTIALS')
    if google_creds:
        cred_length = len(google_creds)
        print(f"✅ GOOGLE_CREDENTIALS exists with length: {cred_length}")
        
        # Check if it's valid JSON
        try:
            json_obj = json.loads(google_creds)
            required_keys = ["type", "project_id", "private_key", "client_email"]
            missing_keys = [key for key in required_keys if key not in json_obj]
            
            if missing_keys:
                print(f"❌ JSON is missing required keys: {missing_keys}")
            else:
                print("✅ JSON contains required service account keys")
                
            # Print important keys to verify
            if "type" in json_obj:
                print(f"  - Credential type: {json_obj['type']}")
            if "project_id" in json_obj:
                print(f"  - Project ID: {json_obj['project_id']}")
            if "client_email" in json_obj:
                print(f"  - Client email: {json_obj['client_email']}")
        except json.JSONDecodeError as e:
            print(f"❌ GOOGLE_CREDENTIALS contains invalid JSON: {e}")
    else:
        print("❌ GOOGLE_CREDENTIALS is not set")
    
    # Check if GOOGLE_APPLICATION_CREDENTIALS exists
    app_creds = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if app_creds:
        print(f"✅ GOOGLE_APPLICATION_CREDENTIALS exists: {app_creds}")
        # Check if file exists
        if os.path.exists(app_creds):
            print(f"✅ Credentials file exists at {app_creds}")
        else:
            print(f"❌ Credentials file does not exist at {app_creds}")
    else:
        print("❌ GOOGLE_APPLICATION_CREDENTIALS is not set")
        
    # Check other environment variables
    print("\n--- Other Environment Variables ---")
    if os.environ.get('SECRET_KEY'):
        print("✅ SECRET_KEY is set")
    else:
        print("❌ SECRET_KEY is not set")
        
    if os.environ.get('AUTHORIZED_USERS'):
        print(f"✅ AUTHORIZED_USERS: {os.environ.get('AUTHORIZED_USERS')}")
    else:
        print("❌ AUTHORIZED_USERS is not set")
    
    # Check if config.setup_credentials() was run
    from projectAron import config
    temp_path = config.setup_credentials()
    print(f"\n✅ config.setup_credentials() returned path: {temp_path}")
    
    # After running setup_credentials, check if the path exists
    if temp_path and os.path.exists(temp_path):
        print(f"✅ Temporary credentials file created at: {temp_path}")
    elif temp_path:
        print(f"❌ Failed to create temporary credentials file at: {temp_path}")
        
    # Print all environment variables for debugging
    print("\n--- All Environment Variables ---")
    for key, value in os.environ.items():
        if key in ['GOOGLE_CREDENTIALS', 'GOOGLE_CLIENT_SECRETS']:
            print(f"{key}: <REDACTED>")
        else:
            print(f"{key}: {value}")
            
if __name__ == "__main__":
    check_environment()
