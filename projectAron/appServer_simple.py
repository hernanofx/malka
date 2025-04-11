from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import os
import json
import secrets
from functools import wraps
from projectAron.codigoARON_simple import get_candidates, create_new_sheet, get_all_sheets

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(16))

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
        # Utilizar la función get_all_sheets para obtener las hojas
        sheet_names = get_all_sheets(spreadsheet_name)
        
        if not sheet_names:
            return jsonify({"error": "No sheets found or access error."}), 400
        
        return jsonify({"sheets": sheet_names})
    
    except Exception as e:
        return jsonify({"error": f"Error al obtener las hojas: {str(e)}"}), 500

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
        new_sheet_url = create_new_sheet(spreadsheet_name, candidates)
        return jsonify({"url": new_sheet_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
