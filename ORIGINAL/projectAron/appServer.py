from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from codigoARONconIA import get_candidates, create_new_sheet, get_all_sheets
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Necesario para la sesión

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# Ruta para la página principal
@app.route('/')
def index():
    return render_template('index.html')

# Ruta de autenticación con Google
@app.route('/login')
def login():
    if 'credentials' not in session:
        # Iniciar el flujo de autenticación de OAuth
        flow = InstalledAppFlow.from_client_secrets_file(
            'credenciales.json', SCOPES)
        credentials = flow.run_local_server(port=0)

        session['credentials'] = credentials_to_dict(credentials)
    return redirect(url_for('index'))

AUTHORIZED_USERS = ['malkasafadie@gmail.com'] #, 'user2@example.com'
# Ruta para obtener las hojas de cálculo de Google Sheets
@app.route('/get_sheets/<spreadsheet_name>', methods=['GET'])
def get_sheets(spreadsheet_name):
    if 'credentials' not in session:
        return redirect(url_for('login'))  # Si no hay credenciales, redirige al login
    
    credentials = Credentials.from_authorized_user_info(session['credentials'])
    
    # Si las credenciales han expirado, necesitamos refrescarlas
    if credentials and credentials.expired and credentials.refresh_token:
        credentials = refresh_credentials(credentials)
        session['credentials'] = credentials_to_dict(credentials)
    
    try:
        # Utilizar tu función get_all_sheets para obtener las hojas
        sheet_names = get_all_sheets(spreadsheet_name)  # Usamos tu función para obtener las hojas
        
        if not sheet_names:
            return jsonify({"error": "No sheets found or access error."}), 400  # Retorna un error si no hay hojas
        
        return jsonify({"sheets": sheet_names})
    
    except Exception as e:
        return jsonify({"error": f"Error al obtener las hojas: {str(e)}"})

# Ruta para obtener candidatos
@app.route('/get_candidates', methods=['POST'])
def get_candidates_route():
    # Obtener los datos del formulario
    spreadsheet_name = request.form.get('spreadsheet_name')
    sheet_names = request.form.getlist('sheet_names')
    top_n = int(request.form.get('top_n'))
    job_description = request.form.get('job_description')

    # Llamar a la función get_candidates con los parámetros proporcionados
    try:
        candidates = get_candidates(spreadsheet_name, sheet_names, job_description, top_n)
        new_sheet_url = create_new_sheet(spreadsheet_name, candidates)  # Llama a create_new_sheet
        return jsonify({"url": new_sheet_url})
    except Exception as e:
        return jsonify({"error": str(e)})

def refresh_credentials(credentials):
    """ Refresca las credenciales utilizando el refresh_token """
    creds = None
    if credentials and credentials.expired and credentials.refresh_token:
        creds = credentials.refresh(Request())
    return creds

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
    app.run(debug=True)
