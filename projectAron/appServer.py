from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from codigoARONconIA import get_candidates, create_new_sheet, get_all_sheets
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import os
import json
from functools import wraps
import secrets
import config

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(16))  # Use environment variable or generate secret key

# Configurar credenciales desde variables de entorno en producción
if os.environ.get('GOOGLE_CREDENTIALS'):
    credentials_path = config.setup_credentials()
    # Usar credentials_path en lugar de ruta fija

# Configuración para OAuth con Google
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly', 'email', 'profile']
AUTHORIZED_USERS = os.environ.get('AUTHORIZED_USERS', 'malkasafadie@gmail.com').split(',')

# Lista de usuarios y contraseñas (para entorno de desarrollo)
# En producción, usa una base de datos o integración con un servicio de autenticación
USERS = {
    'admin@example.com': 'password123',
    'malkasafadie@gmail.com': 'password123'
}

# Decorador para rutas que requieren autenticación
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Ruta para la página principal (protegida)
@app.route('/')
@login_required
def index():
    return render_template('index.html', user=session.get('user'))

# Ruta para el login con credenciales normales
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
            return render_template('login.html', error='Invalid email or password')
    
    return render_template('login.html')

# Ruta para el logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Ruta para iniciar el flujo de autenticación con Google
@app.route('/google-login')
def google_login():
    # Crear un objeto Flow
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secrets.json', SCOPES)
    
    # Definir URI de redirección para Google
    flow.redirect_uri = url_for('google_auth_callback', _external=True)
    
    # Generar URL para autenticación
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')
    
    # Guardar el estado en la sesión
    session['state'] = state
    
    return redirect(authorization_url)

# Callback para autenticación con Google
@app.route('/google-auth-callback')
def google_auth_callback():
    state = session.get('state')
    
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secrets.json', SCOPES, state=state)
    flow.redirect_uri = url_for('google_auth_callback', _external=True)
    
    # Intercambiar código por token
    flow.fetch_token(authorization_response=request.url)
    
    # Obtener credenciales e info del usuario
    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)
    
    # Verificar si el usuario está autorizado
    from googleapiclient.discovery import build
    service = build('oauth2', 'v2', credentials=credentials)
    user_info = service.userinfo().get().execute()
    email = user_info.get('email')
    
    if email in AUTHORIZED_USERS:
        session['user'] = email
        return redirect(url_for('index'))
    else:
        return render_template('login.html', error='Unauthorized user. Please contact the administrator.')

# Ruta para obtener las hojas de cálculo (protegida)
@app.route('/get_sheets/<spreadsheet_name>', methods=['GET'])
@login_required
def get_sheets(spreadsheet_name):
    try:
        # Utilizar tu función get_all_sheets para obtener las hojas
        sheet_names = get_all_sheets(spreadsheet_name)
        
        if not sheet_names:
            return jsonify({"error": "No sheets found or access error."}), 400
        
        return jsonify({"sheets": sheet_names})
    
    except Exception as e:
        return jsonify({"error": f"Error al obtener las hojas: {str(e)}"}), 500

# Ruta para obtener candidatos (protegida)
@app.route('/get_candidates', methods=['POST'])
@login_required
def get_candidates_route():
    # Obtener los datos del formulario
    spreadsheet_name = request.form.get('spreadsheet_name')
    sheet_names = request.form.getlist('sheet_names')
    top_n = int(request.form.get('top_n'))
    job_description = request.form.get('job_description')

    # Llamar a la función get_candidates con los parámetros proporcionados
    try:
        candidates = get_candidates(spreadsheet_name, sheet_names, job_description, top_n)
        new_sheet_url = create_new_sheet(spreadsheet_name, candidates)
        return jsonify({"url": new_sheet_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def refresh_credentials(credentials):
    """ Refresca las credenciales utilizando el refresh_token """
    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    return credentials

def credentials_to_dict(credentials):
    """Convierte las credenciales a un diccionario"""
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

if __name__ == "__main__":
    # En desarrollo, usar host local
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
