import os
import json
import tempfile
import traceback

def setup_credentials():
    """Set up the Google credentials from environment variables in production"""
    try:
        # For credenciales.json (service account)
        if os.environ.get('GOOGLE_CREDENTIALS'):
            print("Found GOOGLE_CREDENTIALS environment variable, creating temporary file")
            # Verify JSON is valid
            try:
                json_data = os.environ.get('GOOGLE_CREDENTIALS')
                json_obj = json.loads(json_data)
                
                # Verify required fields
                required_keys = ["type", "project_id", "private_key", "client_email"]
                missing_keys = [key for key in required_keys if key not in json_obj]
                if missing_keys:
                    print(f"WARNING: JSON is missing required keys: {missing_keys}")
                else:
                    print(f"Credentials JSON validated successfully for project: {json_obj.get('project_id')}")
                
                # Create temporary file with credentials from environment
                fd, path = tempfile.mkstemp(suffix='.json')
                with os.fdopen(fd, 'w') as tmp:
                    tmp.write(json_data)
                
                # Set environment variable to point to this file
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = path
                print(f"Created temporary credentials file at: {path}")
                return path
            except json.JSONDecodeError as e:
                print(f"ERROR: Invalid JSON in GOOGLE_CREDENTIALS: {str(e)}")
                print(f"JSON starts with: {json_data[:50]}..." if 'json_data' in locals() else "No JSON data found")
                return None
            except Exception as e:
                print(f"ERROR creating temporary credentials file: {str(e)}")
                traceback.print_exc()
                return None
        
        # For client_secrets.json (OAuth 2.0)
        if os.environ.get('GOOGLE_CLIENT_SECRETS'):
            print("Found GOOGLE_CLIENT_SECRETS environment variable, creating temporary file")
            try:
                # Create temporary file with client secrets from environment
                fd, path = tempfile.mkstemp(suffix='.json')
                with os.fdopen(fd, 'w') as tmp:
                    tmp.write(os.environ.get('GOOGLE_CLIENT_SECRETS'))
                print(f"Created temporary OAuth client secrets file at: {path}")
                # Return the path to be used in the OAuth flow
                return path
            except Exception as e:
                print(f"ERROR creating temporary OAuth client secrets file: {str(e)}")
                return None
        
        print("WARNING: No Google credentials found in environment variables")
        return None
    except Exception as e:
        print(f"CRITICAL ERROR in setup_credentials: {str(e)}")
        traceback.print_exc()
        return None
