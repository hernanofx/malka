import os
import json
import tempfile
import traceback

def setup_credentials():
    """Set up the Google credentials from environment variables in production"""
    try:
        # Check for Google credentials JSON in environment variable
        if os.environ.get('GOOGLE_CREDENTIALS'):
            print("Using GOOGLE_CREDENTIALS from environment variable")
            try:
                # Parse the JSON to validate and correct any formatting issues
                try:
                    json_creds = json.loads(os.environ.get('GOOGLE_CREDENTIALS'))
                    
                    # Verify and fix common issues with the private key
                    if 'private_key' in json_creds and isinstance(json_creds['private_key'], str):
                        private_key = json_creds['private_key']
                        
                        # Check if the key contains escaped newlines instead of actual newlines
                        if '\\n' in private_key and '\n' not in private_key:
                            print("Correcting '\\n' in private_key to actual newlines")
                            private_key = private_key.replace('\\n', '\n')
                            json_creds['private_key'] = private_key
                        
                        # Make sure the key has proper BEGIN/END markers
                        if not ("-----BEGIN PRIVATE KEY-----" in private_key and "-----END PRIVATE KEY-----" in private_key):
                            print("WARNING: Private key may not be correctly formatted")
                    
                    # Create a temporary file with the corrected JSON
                    fd, path = tempfile.mkstemp(suffix='.json')
                    with os.fdopen(fd, 'w') as tmp:
                        json.dump(json_creds, tmp)
                        
                    print(f"Created temporary credentials file at: {path}")
                    # Return the path to be used for authentication
                    return path
                    
                except json.JSONDecodeError as e:
                    print(f"ERROR parsing GOOGLE_CREDENTIALS as JSON: {str(e)}")
                    # Try to save the raw content to a temporary file as fallback
                    fd, path = tempfile.mkstemp(suffix='.json')
                    with os.fdopen(fd, 'w') as tmp:
                        tmp.write(os.environ.get('GOOGLE_CREDENTIALS'))
                    print(f"Created temporary credentials file (raw content) at: {path}")
                    return path
            except Exception as e:
                print(f"ERROR creating temporary credentials file: {str(e)}")
                traceback.print_exc()
                return None

        # Alternative: Check for client secrets JSON
        if os.environ.get('GOOGLE_CLIENT_SECRETS'):
            print("Using GOOGLE_CLIENT_SECRETS from environment variable")
            try:
                # Similar process for client secrets
                try:
                    json_data = json.loads(os.environ.get('GOOGLE_CLIENT_SECRETS'))
                    fd, path = tempfile.mkstemp(suffix='.json')
                    with os.fdopen(fd, 'w') as tmp:
                        json.dump(json_data, tmp)
                except json.JSONDecodeError:
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
        print("Looking for local credentials file...")
        
        # Check for local credentials file as fallback
        local_paths = [
            "./credenciales.json",
            "./projectAron/credenciales.json",
            "credenciales.json"
        ]
        
        for path in local_paths:
            if os.path.exists(path):
                print(f"Found local credentials file: {path}")
                
                # Verify and fix the credentials file if needed
                try:
                    with open(path, 'r') as f:
                        json_content = json.load(f)
                    
                    # Fix common issues with the private key
                    if 'private_key' in json_content and isinstance(json_content['private_key'], str):
                        private_key = json_content['private_key']
                        if '\\n' in private_key and '\n' not in private_key:
                            print("Correcting '\\n' in private_key to actual newlines in local file")
                            private_key = private_key.replace('\\n', '\n')
                            json_content['private_key'] = private_key
                            
                            # Save the corrected file
                            with open(path, 'w') as f:
                                json.dump(json_content, f)
                                print("Local credentials file corrected and saved")
                
                    return path
                except Exception as e:
                    print(f"WARNING: Could not verify/fix local credentials file: {e}")
                    # Still return the path even if verification failed
                    return path
        
        print("WARNING: No Google credentials found in environment or local files")
        return None
    except Exception as e:
        print(f"CRITICAL ERROR in setup_credentials: {str(e)}")
        traceback.print_exc()
        return None
