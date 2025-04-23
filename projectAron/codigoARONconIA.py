import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from sentence_transformers import SentenceTransformer, util
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.discovery import build
from io import BytesIO
import requests
import fitz  
import docx  
import os
import json
import tempfile
import traceback
from google.oauth2.service_account import Credentials


def authenticate_google_sheets(creds_file="credenciales.json"):
    """
    Autentica con Google Sheets usando credenciales de service account.
    Intenta múltiples métodos de autenticación para mayor robustez.
    """
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # Método 1: GOOGLE_CREDENTIALS como variable de entorno (prioridad alta para Heroku)
        if os.environ.get('GOOGLE_CREDENTIALS'):
            print("Intentando autenticar con GOOGLE_CREDENTIALS desde variable de entorno")
            try:
                # Cargar JSON directamente desde la variable de entorno
                json_creds = json.loads(os.environ.get('GOOGLE_CREDENTIALS'))
                
                # Verificar si hay escapes incorrectos en la clave privada
                if 'private_key' in json_creds and isinstance(json_creds['private_key'], str):
                    if '\\n' in json_creds['private_key'] and '\n' not in json_creds['private_key']:
                        print("Corrigiendo formato de saltos de línea en private_key")
                        json_creds['private_key'] = json_creds['private_key'].replace('\\n', '\n')
                
                # Usar from_service_account_info en lugar de from_json_keyfile_dict para mayor compatibilidad
                creds = Credentials.from_service_account_info(json_creds, scopes=scope)
                client = gspread.authorize(creds)
                print("✅ Autenticado con éxito usando GOOGLE_CREDENTIALS")
                return client
            except json.JSONDecodeError as e:
                print(f"Error parseando JSON de GOOGLE_CREDENTIALS: {e}")
                print("Intentando crear archivo temporal...")
                
                # Crear archivo temporal con el contenido
                fd, temp_path = tempfile.mkstemp(suffix='.json')
                with os.fdopen(fd, 'w') as f:
                    f.write(os.environ.get('GOOGLE_CREDENTIALS'))
                
                # Autenticar usando el archivo temporal
                creds = ServiceAccountCredentials.from_json_keyfile_name(temp_path, scope)
                client = gspread.authorize(creds)
                print(f"✅ Autenticado con éxito usando archivo temporal: {temp_path}")
                return client
            except Exception as e:
                print(f"Error usando GOOGLE_CREDENTIALS: {e}")
                traceback.print_exc()
        
        # Método 2: Usar archivo de credenciales especificado
        if os.path.exists(creds_file):
            print(f"Intentando autenticar con archivo: {creds_file}")
            try:
                # Leer contenido del archivo para verificar y corregir posibles problemas
                with open(creds_file, 'r') as f:
                    json_content = json.load(f)
                
                # Verificar formato de private_key
                if 'private_key' in json_content and isinstance(json_content['private_key'], str):
                    if '\\n' in json_content['private_key'] and '\n' not in json_content['private_key']:
                        print("Corrigiendo formato de saltos de línea en private_key del archivo")
                        json_content['private_key'] = json_content['private_key'].replace('\\n', '\n')
                        
                        # Escribir el archivo corregido
                        with open(creds_file, 'w') as f:
                            json.dump(json_content, f)
                
                # Usar las nuevas credenciales de google.oauth2 para mayor compatibilidad
                creds = Credentials.from_service_account_file(creds_file, scopes=scope)
                client = gspread.authorize(creds)
                print(f"✅ Autenticado con éxito usando archivo: {creds_file}")
                return client
            except Exception as e:
                print(f"Error autenticando con archivo {creds_file}: {e}")
                traceback.print_exc()
        
        # Método 3: Buscar credenciales.json en otros directorios comunes
        possible_paths = [
            './credenciales.json',
            './projectAron/credenciales.json',
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credenciales.json'),
        ]
        
        for path in possible_paths:
            if os.path.exists(path) and path != creds_file:  # Evitar intentar el mismo archivo
                print(f"Intentando autenticar con archivo alternativo: {path}")
                try:
                    # Usar las nuevas credenciales de google.oauth2
                    creds = Credentials.from_service_account_file(path, scopes=scope)
                    client = gspread.authorize(creds)
                    print(f"✅ Autenticado con éxito usando archivo alternativo: {path}")
                    return client
                except Exception as e:
                    print(f"Error autenticando con archivo alternativo {path}: {e}")
        
        # Si llegamos aquí, ningún método funcionó
        raise FileNotFoundError(f"No se encontraron credenciales válidas. Por favor verifica el archivo {creds_file} o la variable de entorno GOOGLE_CREDENTIALS.")
    
    except Exception as e:
        print(f"Error crítico en authenticate_google_sheets: {e}")
        traceback.print_exc()
        raise


def extract_text_from_pdf(pdf_path):
    """ Extrae texto de un archivo PDF """
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text("text") + "\n"
    except Exception as e:
        print(f"Error leyendo PDF {pdf_path}: {e}")
    return text.strip()

def extract_text_from_docx(docx_path):
    """ Extrae texto de un archivo DOCX """
    text = ""
    try:
        doc = docx.Document(docx_path)
        text = "\n".join([p.text for p in doc.paragraphs])
    except Exception as e:
        print(f"Error leyendo DOCX {docx_path}: {e}")
    return text.strip()

def download_file_from_drive(file_id, destination):
    """ Descarga el archivo desde Google Drive, exportando si es necesario """
    try:
        print(f"Descargando archivo con ID: {file_id}")
        
        # Usar la función de autenticación mejorada
        client = authenticate_google_sheets()
        
        # Acceder a las credenciales desde el cliente gspread
        if hasattr(client, 'auth'):
            credentials = client.auth
        else:
            # Fallback a la autenticación directa
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            credentials = Credentials.from_service_account_file("credenciales.json", scopes=scope)
        
        service = build('drive', 'v3', credentials=credentials)
        
        # Obtener metadatos del archivo
        file_metadata = service.files().get(fileId=file_id).execute()
        mime_type = file_metadata.get("mimeType", "")
        
        fh = BytesIO()
        if mime_type == "application/vnd.google-apps.document":  # Es un Google Docs
            request = service.files().export_media(fileId=file_id, mimeType="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            if not destination.endswith(".docx"):  # Evitar doble .docx
                destination += ".docx"
        elif mime_type == "application/pdf": #PDF
            request = service.files().get_media(fileId=file_id)
        elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document": #DOCX normal
            request = service.files().get_media(fileId=file_id)
        else:
            print(f"Tipo de archivo no compatible: {mime_type}")
            return None
        
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        
        # Escribir el archivo descargado
        fh.seek(0)
        with open(destination, 'wb') as f:
            f.write(fh.read())

        if os.path.exists(destination):
            print(f"Archivo descargado correctamente: {destination}")
        else:
            print(f"Error: El archivo {destination} no fue creado.")

        return destination  # Retorna la ruta del archivo descargado

    except Exception as e:
        print(f"Error al descargar el archivo desde Google Drive: {e}")
        traceback.print_exc()
        return None


def extract_text_from_pdf_online(file_id):
    """ Extrae texto de un archivo PDF desde Google Drive usando el ID """
    try:
        pdf_file_path = "./temp_pdf_file.pdf"
        download_file_from_drive(file_id, pdf_file_path)
        return extract_text_from_pdf(pdf_file_path)  # Extrae el texto después de descargar
    except Exception as e:
        print(f"Error procesando el PDF con ID {file_id}: {e}")
        return ""

def extract_text_from_docx_online(file_id):
    """ Extrae texto de un archivo DOCX desde Google Drive usando el ID """
    try:
        docx_file_path = "./temp_docx_file.docx"
        download_file_from_drive(file_id, docx_file_path)
        text = extract_text_from_docx(docx_file_path)  # Extrae el texto después de descargar

        # 🔥 Eliminar el archivo después de extraer el texto
        if os.path.exists(docx_file_path):
            os.remove(docx_file_path)
            print(f"Archivo temporal eliminado: {docx_file_path}")

        return text
    except Exception as e:
        print(f"Error procesando el DOCX con ID {file_id}: {e}")
        return ""


def get_candidates(spreadsheet_name, sheet_names, job_description, top_n):
    # Usar la función de autenticación mejorada sin especificar ruta
    client = authenticate_google_sheets()
    
    expected_headers = ["Stage", "Applicant", "Resume", "Information", "Interview link", "Phone Number", "E-mail", "Client", "idResume", "idInformation", "JOB DESCRIPTION"]
    all_candidates = []
    
    # Manejar caso especial para "arondb" (insensible a mayúsculas/minúsculas)
    if isinstance(spreadsheet_name, str) and spreadsheet_name.lower() == "arondb":
        spreadsheet_name = "1EqsYq50pfSoZ5YM4AHKvqEUWT18CzCdgol6mWtRPTfU"
        print(f"Usando ID conocido para ARONDB: {spreadsheet_name}")
    
    for sheet_name in sheet_names:
        try:
            # Intentar abrir primero por ID, luego por nombre
            try:
                sheet = client.open_by_key(spreadsheet_name).worksheet(sheet_name)
            except:
                sheet = client.open(spreadsheet_name).worksheet(sheet_name)
                
            data = sheet.get_all_values()
            
            if not data:
                continue  # Saltar hojas vacías
            
            header_row = data[0]  # Primera fila con los encabezados
            
            # Verificación flexible de encabezados
            available_headers = set(header_row)
            missing_headers = [h for h in expected_headers if h not in available_headers]
            if missing_headers:
                print(f"Advertencia: La hoja '{sheet_name}' no tiene algunos encabezados esperados: {missing_headers}")
                continue
            
            # Obtener índices de columnas para cada encabezado esperado
            header_indices = [header_row.index(header) for header in expected_headers]
            
            # Filtrar las filas de datos
            for row in data[1:]:  # Omitir encabezados
                if len(row) >= len(expected_headers):
                    filtered_row = [row[i] if i < len(row) else "" for i in header_indices]
                    all_candidates.append(filtered_row)
        except Exception as e:
            print(f"Error procesando hoja {sheet_name}: {e}")
            continue
    
    # Convertir a DataFrame
    df = pd.DataFrame(all_candidates, columns=expected_headers)
    # Filtrar candidatos que no tienen ni idResume ni idInformation
    df = df[(df["idResume"].str.strip() != "") | (df["idInformation"].str.strip() != "")]

    if df.empty:
        print("No hay candidatos disponibles en las hojas especificadas.")
        return pd.DataFrame(columns=["Applicant", "Resume", "Information", "Interview link", "Phone Number", "E-mail", "Client", "similarity"])
    
    # Cargar modelo de embeddings
    #model = SentenceTransformer("paraphrase-MiniLM-L6-v2")
    #model = SentenceTransformer("BAAI/bge-large-en")
    model = SentenceTransformer("sentence-transformers/all-MPNet-base-v2")  # Captura relaciones semánticas más detalladas

    # Extraer texto real de los archivos
    extracted_texts = []
    for _, row in df.iterrows():
        resume_text = extract_text_from_pdf_online(row["idResume"]) if row["idResume"] else ""
        info_text = extract_text_from_docx_online(row["idInformation"]) if row["idInformation"] else ""
        combined_text = resume_text + " " + info_text
        extracted_texts.append(combined_text)
    
    df["combined_text"] = extracted_texts
    
    job_embedding = model.encode(job_description, convert_to_tensor=True)
    candidate_embeddings = model.encode(df["combined_text"].tolist(), convert_to_tensor=True)
    
    # Calcular similitud de coseno
    similarities = util.pytorch_cos_sim(job_embedding, candidate_embeddings).squeeze().tolist()
    df["similarity"] = similarities
    
    top_candidates = df.nlargest(top_n, "similarity")
    return top_candidates[["Applicant", "Resume", "Information", "Interview link", "Phone Number", "E-mail", "Client", "similarity"]]


def create_new_sheet(spreadsheet_id, results):
    # Usar la función de autenticación mejorada
    client = authenticate_google_sheets()
    
    # Manejar caso especial para "arondb"
    if isinstance(spreadsheet_id, str) and spreadsheet_id.lower() == "arondb":
        spreadsheet_id = "1EqsYq50pfSoZ5YM4AHKvqEUWT18CzCdgol6mWtRPTfU"
        print(f"Usando ID conocido para ARONDB: {spreadsheet_id}")
    
    # Intentar abrir primero por ID, luego por nombre
    try:
        sheet = client.open_by_key(spreadsheet_id)
    except Exception as e:
        print(f"Error abriendo por ID, intentando por nombre: {e}")
        sheet = client.open(spreadsheet_id)

    # Verificar si la hoja 'Candidates' ya existe
    existing_sheets = sheet.worksheets()
    sheet_names = [s.title for s in existing_sheets]

    # Si la hoja 'Candidates' existe, la eliminamos
    if "Candidates" in sheet_names:
        print("La hoja 'Candidates' ya existe. Eliminando...")
        existing_sheet = sheet.worksheet("Candidates")
        sheet.del_worksheet(existing_sheet)

    # Crear nueva hoja 'Candidates'
    new_sheet = sheet.add_worksheet(title="Candidates", rows="100", cols="10")

    # Insertar los resultados
    data = [list(results.columns)] + results.values.tolist()  # Incluyendo los encabezados
    new_sheet.append_rows(data, value_input_option='RAW')  # Usamos append_rows para insertar los datos

    # Construir la URL para la interfaz web de Google Sheets (en lugar de la API)
    spreadsheet_url = sheet.url
    
    # Extraer el ID del documento del URL
    if '/d/' in spreadsheet_url:
        parts = spreadsheet_url.split('/d/')
        if len(parts) > 1:
            doc_id = parts[1].split('/')[0]
            # Construir URL de la interfaz web que no requiere autenticación
            frontend_url = f"https://docs.google.com/spreadsheets/d/{doc_id}/edit#gid={new_sheet.id}"
            print(f"URL creada para la interfaz web: {frontend_url}")
            return frontend_url
    
    # Si no podemos construir la URL de la interfaz web, devolvemos la URL directa
    direct_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit#gid={new_sheet.id}"
    print(f"URL directa creada: {direct_url}")
    return direct_url


def get_all_sheets(spreadsheet_name):
    # Obtiene todas las hojas (visibles y ocultas) de un Google Sheets 
    try:
        # Autenticarse usando la función mejorada
        client = authenticate_google_sheets()
        
        # Manejar caso especial para "arondb"
        if isinstance(spreadsheet_name, str) and spreadsheet_name.lower() == "arondb":
            spreadsheet_name = "1EqsYq50pfSoZ5YM4AHKvqEUWT18CzCdgol6mWtRPTfU"
            print(f"Usando ID conocido para ARONDB: {spreadsheet_name}")
        
        # Intentar abrir primero por ID, luego por nombre
        try:
            sheets = client.open_by_key(spreadsheet_name).worksheets()
        except:
            sheets = client.open(spreadsheet_name).worksheets()
        
        # Obtener los nombres de las hojas
        sheet_names = [sheet.title for sheet in sheets]
        print(f"Hojas encontradas: {sheet_names}")

        return sheet_names  # Retorna los nombres de las hojas
        
    except Exception as e:
        print(f"Error al obtener las hojas: {e}")
        traceback.print_exc()
        return []

