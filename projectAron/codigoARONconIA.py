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
from google.oauth2.service_account import Credentials


def authenticate_google_sheets(creds_file):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
    client = gspread.authorize(creds)
    return client

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
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credenciales.json", scope)
        service = build('drive', 'v3', credentials=creds)
        
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
    return new_sheet.url  # Retorna la URL de la nueva hoja


def get_all_sheets(spreadsheet_name):
    #Obtiene todas las hojas (visibles y ocultas) de un Google Sheets 
    try:
        # Autenticarse y obtener el cliente de gspread y las credenciales de la API
        client = authenticate_google_sheets("credenciales.json")
        sheets = client.open(spreadsheet_name).worksheets()
        
        # Obtener los nombres de las hojas
        sheet_names = [sheet.title for sheet in sheets]

        return sheet_names  # Retorna los nombres de las hojas
        
    except Exception as e:
        print(f"Error al obtener las hojas: {e}")
        return []

