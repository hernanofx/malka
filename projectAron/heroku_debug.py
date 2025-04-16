"""
Script para diagnosticar la aplicación en Heroku
Ejecuta con: heroku run python -m projectAron.heroku_debug
"""
import os
import json
import sys
import traceback

def check_environment():
    """Check environment variables and system information in Heroku"""
    print("\n=== HEROKU DEBUG INFO ===")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    
    # Verify if running on Heroku
    is_heroku = "DYNO" in os.environ
    print(f"Running on Heroku: {'Yes' if is_heroku else 'No'}")
    
    # List all important directories and files
    print("\n== Directory Structure ==")
    try:
        dirs = os.listdir('.')
        print(f"Root directory: {dirs}")
        
        if 'projectAron' in dirs:
            aron_dir = os.listdir('projectAron')
            print(f"projectAron directory: {aron_dir}")
            
            # Check if credenciales.json exists
            if 'credenciales.json' in aron_dir:
                print("✅ credenciales.json exists in projectAron directory")
                # Try to validate the file
                try:
                    with open('projectAron/credenciales.json', 'r') as f:
                        creds = json.loads(f.read())
                    print(f"✅ credenciales.json is valid JSON")
                    print(f"  - Project ID: {creds.get('project_id')}")
                    print(f"  - Client email: {creds.get('client_email')}")
                except Exception as e:
                    print(f"❌ Error reading credenciales.json: {e}")
            else:
                print("❌ credenciales.json NOT found in projectAron directory")
                
    except Exception as e:
        print(f"Error listing directories: {e}")
        
    # Check environment variables
    print("\n== Environment Variables ==")
    env_vars = {
        'PORT': os.environ.get('PORT'),
        'DYNO': os.environ.get('DYNO'),
        'GOOGLE_CREDENTIALS': os.environ.get('GOOGLE_CREDENTIALS', '')[:50] + '...' if os.environ.get('GOOGLE_CREDENTIALS') else None,
        'GOOGLE_APPLICATION_CREDENTIALS': os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'),
        'SECRET_KEY': os.environ.get('SECRET_KEY', '')[:10] + '...' if os.environ.get('SECRET_KEY') else None,
    }
    
    for key, value in env_vars.items():
        status = "✅" if value else "❌"
        print(f"{status} {key}: {value}")
        
    # Try importing important modules
    print("\n== Module Imports ==")
    modules = ['gspread', 'oauth2client', 'flask', 'pandas', 'sklearn']
    
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module}: imported successfully")
        except ImportError:
            print(f"❌ {module}: import failed")
            
    # Test authentication
    print("\n== Google Sheets Authentication Test ==")
    try:
        from projectAron.codigoARON_simple import authenticate_google_sheets
        client = authenticate_google_sheets()
        print(f"✅ authenticate_google_sheets returned a client successfully")
        
        # Test simple operation
        spreadsheet_id = "1EqsYq50pfSoZ5YM4AHKvqEUWT18CzCdgol6mWtRPTfU"
        try:
            sheet = client.open_by_key(spreadsheet_id)
            worksheets = sheet.worksheets()
            print(f"✅ Successfully opened test spreadsheet with {len(worksheets)} worksheets")
            print(f"  - Worksheet names: {[ws.title for ws in worksheets]}")
        except Exception as e:
            print(f"❌ Error opening test spreadsheet: {e}")
    except Exception as e:
        print(f"❌ Error in authentication test: {e}")
        traceback.print_exc()
        
    # Recommendation
    print("\n== Recommendations ==")
    if not os.environ.get('GOOGLE_CREDENTIALS'):
        print("1. Set the GOOGLE_CREDENTIALS environment variable:")
        print("   heroku config:set GOOGLE_CREDENTIALS=\"$(cat projectAron/credenciales.json)\"")
    
    if 'credenciales.json' not in os.listdir('projectAron') if 'projectAron' in os.listdir('.') else []:
        print("2. Make sure credenciales.json is included in your git repository:")
        print("   - Check your .gitignore file to ensure it doesn't exclude *.json files")
        print("   - Commit and push credentials: git add projectAron/credenciales.json && git commit -m \"Add credentials\" && git push")

if __name__ == "__main__":
    try:
        check_environment()
    except Exception as e:
        print(f"Critical error in debug script: {e}")
        traceback.print_exc()