"""
Debug script to check environment variables and auth state
"""
import os
import json
import sys
import traceback

def check_environment():
    """Check environment variables related to Google authentication"""
    print("=== Environment Variables Debug ===")
    
    # Check for Heroku-specific environment variables
    if os.environ.get('DYNO'):
        print("✅ Running on Heroku")
    else:
        print("⚠️ Not running on Heroku")
        
    # Check PORT variable
    if os.environ.get('PORT'):
        print(f"✅ PORT is set to: {os.environ.get('PORT')}")
    else:
        print("⚠️ PORT is not set")
    
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
                
            # Check if private_key looks valid
            if "private_key" in json_obj:
                private_key = json_obj['private_key']
                if "-----BEGIN PRIVATE KEY-----" in private_key and "-----END PRIVATE KEY-----" in private_key:
                    print("✅ Private key format looks valid")
                else:
                    print("❌ Private key appears to be malformed")
                    # Check for common issues
                    if "\\n" in private_key:
                        print("   - Private key contains literal '\\n' characters, should be actual line breaks")
                    if private_key.count("\\\\n") > 0:
                        print("   - Private key contains double-escaped newlines '\\\\n'")
        except json.JSONDecodeError as e:
            print(f"❌ GOOGLE_CREDENTIALS contains invalid JSON: {e}")
            print(f"First 100 characters: {google_creds[:100]}...")
    else:
        print("❌ GOOGLE_CREDENTIALS is not set")
    
    # Check if GOOGLE_APPLICATION_CREDENTIALS exists
    app_creds = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if app_creds:
        print(f"✅ GOOGLE_APPLICATION_CREDENTIALS exists: {app_creds}")
        # Check if file exists
        if os.path.exists(app_creds):
            print(f"✅ Credentials file exists at {app_creds}")
            try:
                with open(app_creds, 'r') as f:
                    creds_content = f.read()
                    if len(creds_content) > 0:
                        print(f"✅ Credentials file has content (length: {len(creds_content)})")
                    else:
                        print("❌ Credentials file exists but is empty")
            except Exception as e:
                print(f"❌ Error reading credentials file: {e}")
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
    
    # Try importing and using the important modules
    print("\n--- Module Import Check ---")
    try:
        import gspread
        print("✅ gspread module imported successfully")
    except ImportError as e:
        print(f"❌ Error importing gspread: {e}")
        
    try:
        from oauth2client.service_account import ServiceAccountCredentials
        print("✅ oauth2client.service_account.ServiceAccountCredentials imported successfully")
    except ImportError as e:
        print(f"❌ Error importing oauth2client: {e}")
    
    # Check if config.setup_credentials() works
    print("\n--- Config Module Test ---")
    try:
        from projectAron import config
        print("✅ config module imported successfully")
        
        try:
            temp_path = config.setup_credentials()
            if temp_path:
                print(f"✅ config.setup_credentials() returned path: {temp_path}")
                # After running setup_credentials, check if the path exists
                if os.path.exists(temp_path):
                    print(f"✅ Temporary credentials file created at: {temp_path}")
                else:
                    print(f"❌ Temporary credentials file was not created at: {temp_path}")
            else:
                print("❌ config.setup_credentials() returned None")
        except Exception as e:
            print(f"❌ Error running config.setup_credentials(): {e}")
            traceback.print_exc()
    except ImportError as e:
        print(f"❌ Error importing config module: {e}")
        
    # Try to authenticate with Google directly
    print("\n--- Google Authentication Test ---")
    try:
        from projectAron.codigoARON_simple import authenticate_google_sheets
        print("✅ authenticate_google_sheets function imported")
        
        try:
            client = authenticate_google_sheets()
            print("✅ Google authentication successful!")
            
            # Test the client with a simple operation
            try:
                # Just try to open a known spreadsheet
                sheet = client.open_by_key("1EqsYq50pfSoZ5YM4AHKvqEUWT18CzCdgol6mWtRPTfU")
                print(f"✅ Successfully opened test spreadsheet with {len(sheet.worksheets())} worksheets")
            except Exception as e:
                print(f"❌ Error opening test spreadsheet: {e}")
        except Exception as e:
            print(f"❌ Error authenticating with Google: {e}")
            traceback.print_exc()
    except ImportError as e:
        print(f"❌ Error importing authentication function: {e}")
        
    # Print a summary of all environment variables for debugging
    print("\n--- All Environment Variables ---")
    for key, value in sorted(os.environ.items()):
        if key in ['GOOGLE_CREDENTIALS', 'GOOGLE_CLIENT_SECRETS', 'SECRET_KEY']:
            print(f"{key}: <REDACTED>")
        else:
            print(f"{key}: {value}")
            
if __name__ == "__main__":
    try:
        check_environment()
    except Exception as e:
        print(f"CRITICAL ERROR in check_environment: {e}")
        traceback.print_exc()
