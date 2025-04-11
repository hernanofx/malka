import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from io import BytesIO
import os
import tempfile
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import docx
import io
import json

def authenticate_google_sheets(creds_file):
    # Si estamos en Heroku, usar variables de entorno para las credenciales
    if os.environ.get('GOOGLE_CREDENTIALS'):
        # Crear archivo temporal con las credenciales
        fd, temp_path = tempfile.mkstemp()
        with os.fdopen(fd, 'w') as f:
            f.write(os.environ.get('GOOGLE_CREDENTIALS'))
        creds_file = temp_path

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
    client = gspread.authorize(creds)
    
    # Eliminar archivo temporal si fue creado
    if os.environ.get('GOOGLE_CREDENTIALS') and os.path.exists(temp_path):
        os.remove(temp_path)
        
    return client

def download_file_from_drive(file_id, destination=None):
    """Descarga archivo desde Google Drive y retorna su contenido como texto"""
    try:
        # Configurar credenciales desde variables de entorno o archivo
        if os.environ.get('GOOGLE_CREDENTIALS'):
            fd, temp_path = tempfile.mkstemp()
            with os.fdopen(fd, 'w') as f:
                f.write(os.environ.get('GOOGLE_CREDENTIALS'))
            creds_file = temp_path
        else:
            creds_file = "credenciales.json"
            
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
        service = build('drive', 'v3', credentials=creds)
        
        # Limpiar archivo temporal
        if os.environ.get('GOOGLE_CREDENTIALS') and os.path.exists(temp_path):
            os.remove(temp_path)
        
        # Obtener metadatos del archivo
        file_metadata = service.files().get(fileId=file_id).execute()
        mime_type = file_metadata.get("mimeType", "")
        
        # Descargar contenido a memoria
        request = None
        if mime_type == "application/vnd.google-apps.document":
            request = service.files().export_media(fileId=file_id, 
                                                mimeType="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        else:
            request = service.files().get_media(fileId=file_id)
            
        if not request:
            return ""
            
        file_content = BytesIO()
        downloader = MediaIoBaseDownload(file_content, request)
        
        done = False
        while not done:
            _, done = downloader.next_chunk()
            
        file_content.seek(0)
        
        # Extraer texto según el tipo de archivo
        if mime_type == "application/vnd.google-apps.document" or mime_type.endswith(".docx"):
            try:
                doc = docx.Document(file_content)
                return "\n".join([para.text for para in doc.paragraphs])
            except Exception as e:
                print(f"Error extrayendo texto de DOCX: {e}")
        elif mime_type == "application/pdf":
            try:
                # Forma ligera de extraer texto de PDF
                from pypdf2 import PdfFileReader
                pdf = PdfFileReader(file_content)
                text = ""
                for page_num in range(pdf.getNumPages()):
                    text += pdf.getPage(page_num).extractText() + "\n"
                return text
            except Exception as e:
                print(f"Error extrayendo texto de PDF: {e}")
        
        return ""
            
    except Exception as e:
        print(f"Error al descargar archivo: {e}")
        return ""

def get_candidates(spreadsheet_name, sheet_names, job_description, top_n):
    client = authenticate_google_sheets("credenciales.json")
    
    expected_headers = ["Stage", "Applicant", "Resume", "Information", "Interview link", "Phone Number", "E-mail", "Client", "idResume", "idInformation", "JOB DESCRIPTION"]
    all_candidates = []
    
    for sheet_name in sheet_names:
        sheet = client.open(spreadsheet_name).worksheet(sheet_name)
        data = sheet.get_all_values()
        
        if not data:
            continue  # Saltar hojas vacías
        
        header_row = data[0]  # Primera fila con los encabezados
        
        if not set(expected_headers).issubset(set(header_row)):
            print(f"Advertencia: La hoja '{sheet_name}' no tiene los encabezados esperados.")
            continue
        
        header_indices = [header_row.index(header) for header in expected_headers]
        
        # Filtrar las filas de datos
        for row in data[1:]:  # Omitir encabezados
            filtered_row = [row[i] if i < len(row) else "" for i in header_indices]
            all_candidates.append(filtered_row)
    
    # Convertir a DataFrame
    df = pd.DataFrame(all_candidates, columns=expected_headers)
    # Filtrar candidatos que no tienen ni idResume ni idInformation
    df = df[(df["idResume"].str.strip() != "") | (df["idInformation"].str.strip() != "")]

    if df.empty:
        print("No hay candidatos disponibles en las hojas especificadas.")
        return pd.DataFrame()
    
    # Extraer texto real de los archivos
    extracted_texts = []
    for _, row in df.iterrows():
        resume_text = download_file_from_drive(row["idResume"]) if row["idResume"] else ""
        info_text = download_file_from_drive(row["idInformation"]) if row["idInformation"] else ""
        combined_text = resume_text + " " + info_text
        extracted_texts.append(combined_text)
    
    df["combined_text"] = extracted_texts
    
    # Usar TF-IDF y similitud de coseno (mucho más ligero que sentence-transformers)
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform([job_description] + df["combined_text"].tolist())
    
    # Calcular similitud entre la descripción del trabajo y cada candidato
    job_vector = tfidf_matrix[0:1]
    candidate_vectors = tfidf_matrix[1:]
    similarities = cosine_similarity(job_vector, candidate_vectors).flatten()
    
    df["similarity"] = similarities
    
    top_candidates = df.nlargest(top_n, "similarity")
    return top_candidates[["Applicant", "Resume", "Information", "Interview link", "Phone Number", "E-mail", "Client", "similarity"]]

def create_new_sheet(spreadsheet_id, results):
    client = authenticate_google_sheets("credenciales.json")
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

    # Retornar la URL de la nueva hoja
    return new_sheet.url

def get_all_sheets(spreadsheet_name):
    """Obtiene todas las hojas de un Google Sheets"""
    try:
        # Autenticarse y obtener el cliente de gspread
        client = authenticate_google_sheets("credenciales.json")
        sheets = client.open(spreadsheet_name).worksheets()
        
        # Obtener los nombres de las hojas
        sheet_names = [sheet.title for sheet in sheets]

        return sheet_names
        
    except Exception as e:
        print(f"Error al obtener las hojas: {e}")
        return []
