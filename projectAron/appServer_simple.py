from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os
import json
import secrets
import traceback
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(16))

# Inicializar credenciales al inicio
try:
    from projectAron import config
    credentials_path = config.setup_credentials()
    if credentials_path:
        app.logger.info(f"Initialized credentials at startup: {credentials_path}")
    else:
        app.logger.warning("Failed to initialize credentials at startup")
except Exception as e:
    app.logger.error(f"Error initializing credentials: {e}")
    traceback.print_exc()

# Lista de usuarios autorizados (para entorno de desarrollo)
USERS = {
    'admin@example.com': 'password123',
    'malkasafadie@gmail.com': 'password123'
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Ruta para la página principal (protegida)
@app.route('/')
def index():
    return render_template('index.html')

# Ruta para login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Verificar credenciales
        if email in USERS and USERS[email] == password:
            session['user'] = email
            return redirect(url_for('index'))
        else:
            app.logger.warning(f"Failed login attempt for email: {email}")
            return render_template('login.html', error='Invalid email or password')
    
    return render_template('login.html')

# Ruta para logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Ruta para obtener las hojas de cálculo
@app.route('/get_sheets/<spreadsheet_name>', methods=['GET'])
def get_sheets(spreadsheet_name):
    try:
        # Import here to avoid initial load issues
        from projectAron.codigoARON_simple import get_all_sheets
        
        # Print debugging information - this will show in Heroku logs
        app.logger.info(f"Fetching sheets for spreadsheet: {spreadsheet_name}")
        has_credentials = bool(os.environ.get('GOOGLE_CREDENTIALS'))
        app.logger.info(f"GOOGLE_CREDENTIALS environment variable exists: {has_credentials}")
        if has_credentials:
            creds_length = len(os.environ.get('GOOGLE_CREDENTIALS', ''))
            app.logger.info(f"GOOGLE_CREDENTIALS length: {creds_length}")
            # Verify JSON is valid
            try:
                json.loads(os.environ.get('GOOGLE_CREDENTIALS'))
                app.logger.info("GOOGLE_CREDENTIALS contains valid JSON")
            except json.JSONDecodeError as e:
                app.logger.error(f"GOOGLE_CREDENTIALS contains invalid JSON: {e}")
        
        # Handle direct spreadsheet URL case
        if spreadsheet_name.startswith('http'):
            # Extract ID from URL if it's a Google Sheets URL
            import re
            match = re.search(r'/d/([a-zA-Z0-9-_]+)', spreadsheet_name)
            if match:
                spreadsheet_id = match.group(1)
                app.logger.info(f"Extracted spreadsheet ID from URL: {spreadsheet_id}")
                spreadsheet_name = spreadsheet_id
        
        # Check if working with hardcoded spreadsheet name
        if spreadsheet_name.lower() == "arondb":
            spreadsheet_name = "1EqsYq50pfSoZ5YM4AHKvqEUWT18CzCdgol6mWtRPTfU"
            app.logger.info(f"Using ARONDB spreadsheet ID: {spreadsheet_name}")
            
        # Utilizar la función get_all_sheets para obtener las hojas
        sheet_names = get_all_sheets(spreadsheet_name)
        
        app.logger.info(f"Found sheets: {sheet_names}")
        
        if not sheet_names:
            return jsonify({"error": "No sheets found or access error."}), 400
        
        return jsonify({"sheets": sheet_names})
    
    except Exception as e:
        app.logger.error(f"Error getting sheets: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({"error": f"Error al obtener las hojas: {str(e)}"}), 500

# Ruta para obtener candidatos
@app.route('/get_candidates', methods=['POST'])
def get_candidates_route():
    try:
        # Import here to avoid initial load issues
        from projectAron.codigoARON_simple import get_candidates, create_new_sheet
        
        # Obtener los datos del formulario
        spreadsheet_name = request.form.get('spreadsheet_name')
        sheet_names = request.form.getlist('sheet_names')
        top_n = int(request.form.get('top_n'))
        job_description = request.form.get('job_description')

        # Llamar a la función get_candidates con los parámetros proporcionados
        candidates = get_candidates(spreadsheet_name, sheet_names, job_description, top_n)
        new_sheet_url = create_new_sheet(spreadsheet_name, candidates)
        return jsonify({"url": new_sheet_url})
    except ImportError as e:
        app.logger.error(f"Import error: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({"error": f"Error de importación: {str(e)}. Es posible que falten dependencias en el servidor."}), 500
    except Exception as e:
        app.logger.error(f"General error: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
