import os
import json
import tempfile

def setup_credentials():
    """Set up the Google credentials from environment variables in production"""
    
    # For credenciales.json (service account)
    if os.environ.get('GOOGLE_CREDENTIALS'):
        # Create temporary file with credentials from environment
        fd, path = tempfile.mkstemp(suffix='.json')
        with os.fdopen(fd, 'w') as tmp:
            tmp.write(os.environ.get('GOOGLE_CREDENTIALS'))
        # Set environment variable to point to this file
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = path
        return path
    
    # For client_secrets.json (OAuth 2.0)
    if os.environ.get('GOOGLE_CLIENT_SECRETS'):
        # Create temporary file with client secrets from environment
        fd, path = tempfile.mkstemp(suffix='.json')
        with os.fdopen(fd, 'w') as tmp:
            tmp.write(os.environ.get('GOOGLE_CLIENT_SECRETS'))
        # Return the path to be used in the OAuth flow
        return path
    
    return None
