import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import tempfile
import json
from io import BytesIO
import sys

# Try to import potentially problematic libraries with alternatives
try:
    import pandas as pd
except ImportError:
    print("Error importing pandas. Using alternative implementation.")
    # Simple DataFrame implementation
    class DataFrame:
        def __init__(self, data=None, columns=None):
            self.data = data or []
            self.columns = columns or []
            
        def __getitem__(self, col):
            if isinstance(col, list):
                # Return a new DataFrame with only the specified columns
                idx = [self.columns.index(c) for c in col]
                new_data = []
                for row in self.data:
                    new_data.append([row[i] for i in idx])
                return DataFrame(new_data, col)
            else:
                # Return the values for a single column
                idx = self.columns.index(col)
                return ColumnSeries([row[idx] for row in self.data])
        
        def nlargest(self, n, col):
            col_idx = self.columns.index(col)
            sorted_data = sorted(self.data, key=lambda x: float(x[col_idx]) if x[col_idx] else 0, reverse=True)
            return DataFrame(sorted_data[:n], self.columns)
    
    class ColumnSeries:
        def __init__(self, data):
            self.data = data
        
        def strip(self):
            return self
        
        def __ne__(self, other):
            return [x != other for x in self.data]
    
    pd = type('', (), {})()
    pd.DataFrame = DataFrame

try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
except ImportError:
    print("Error importing googleapiclient. Some functionality may be limited.")

try:
    import docx
except ImportError:
    print("Error importing python-docx. Will use simplified text extraction.")
    docx = None

# Simplified TF-IDF implementation if scikit-learn is not available
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    print("Error importing scikit-learn. Using simplified implementation.")
    
    def cosine_similarity(a, b):
        """Very simplified cosine similarity"""
        import math
        
        # Convert sparse matrices to lists
        if hasattr(a, 'toarray'):
            a = a.toarray()[0]
        if hasattr(b, 'toarray'):
            b_arrays = [x.toarray()[0] for x in b]
        else:
            b_arrays = b
            
        results = []
        for b_vec in b_arrays:
            # Calculate dot product
            dot_product = sum(x*y for x, y in zip(a, b_vec))
            
            # Calculate magnitudes
            mag_a = math.sqrt(sum(x*x for x in a))
            mag_b = math.sqrt(sum(x*x for x in b_vec))
            
            # Calculate cosine similarity
            if mag_a and mag_b:
                similarity = dot_product / (mag_a * mag_b)
            else:
                similarity = 0
                
            results.append(similarity)
        
        return [results]
    
    # Simplified TF-IDF vectorizer
    class SimpleTfidfVectorizer:
        def __init__(self, stop_words=None):
            self.stop_words = stop_words or []
            self.vocabulary_ = {}
            self.idf_ = {}
            
        def fit_transform(self, texts):
            # Tokenize and count
            all_terms = set()
            for text in texts:
                for word in self._tokenize(text):
                    all_terms.add(word)
            
            # Build vocabulary
            self.vocabulary_ = {term: i for i, term in enumerate(all_terms)}
            
            # Build document-term matrix
            doc_term_matrix = []
            for text in texts:
                term_counts = self._count_terms(text)
                vector = [0] * len(self.vocabulary_
                )
                for term, count in term_counts.items():
                    if term in self.vocabulary_:
                        vector[self.vocabulary_[term]] = count
                doc_term_matrix.append(vector)
            
            return doc_term_matrix
        
        def _tokenize(self, text):
            """Simple tokenization"""
            words = text.lower().split()
            return [w for w in words if w not in self.stop_words]
        
        def _count_terms(self, text):
            """Count term frequencies"""
            counts = {}
            for word in self._tokenize(text):
                counts[word] = counts.get(word, 0) + 1
            return counts
    
    TfidfVectorizer = SimpleTfidfVectorizer

def authenticate_google_sheets(creds_file="credenciales.json"):
    """
    Authenticate with Google Sheets API using service account credentials.
    Prioritizes environment variables over file credentials.
    """
    try:
        # Check for credentials in environment variables first
        if os.environ.get('GOOGLE_CREDENTIALS'):
            print("Using credentials from environment variable")
            # Create JSON directly from the environment variable
            json_creds = json.loads(os.environ.get('GOOGLE_CREDENTIALS'))
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(json_creds, scope)
            client = gspread.authorize(creds)
            return client
        else:
            # Only try file-based authentication if environment variable is not available
            print(f"Using credentials from file: {creds_file}")
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
            client = gspread.authorize(creds)
            return client
    except Exception as e:
        print(f"Error authenticating with Google Sheets: {e}")
        raise

def download_file_from_drive(file_id, destination=None):
    """Descarga archivo desde Google Drive y retorna su contenido como texto"""
    try:
        # Create authentication using the same approach as above
        if os.environ.get('GOOGLE_CREDENTIALS'):
            print("Using credentials from environment variable for Drive API")
            json_creds = json.loads(os.environ.get('GOOGLE_CREDENTIALS'))
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(json_creds, scope)
        else:
            creds_file = "credenciales.json"
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
            
        service = build('drive', 'v3', credentials=creds)
        
        # Obtener metadatos del archivo
        file_metadata = service.files().get(fileId=file_id).execute()
        mime_type = file_metadata.get("mimeType", "")
        
        # Descargar contenido a memoria
        request = None
        if mime_type == "application/vnd.google-apps.document":
            request = service.files().export_media(fileId=file_id, 
                                                mimeType="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        else:
            creds_file = "credenciales.json"dia(fileId=file_id)
            
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
        service = build('drive', 'v3', credentials=creds)
        file_content = BytesIO()
        # Limpiar archivo temporalwnload(file_content, request)
        if os.environ.get('GOOGLE_CREDENTIALS') and os.path.exists(temp_path):
            os.remove(temp_path)
        while not done:
        # Obtener metadatos del archivohunk()
        file_metadata = service.files().get(fileId=file_id).execute()
        mime_type = file_metadata.get("mimeType", "")
        
        # Descargar contenido a memoriae archivo
        request = None= "application/vnd.google-apps.document" or mime_type.endswith(".docx"):
        if mime_type == "application/vnd.google-apps.document":
            request = service.files().export_media(fileId=file_id, 
                                                mimeType="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        else:       return "\n".join([para.text for para in doc.paragraphs])
            request = service.files().get_media(fileId=file_id)
                    # Simplified text extraction
        if not request:tent = file_content.read()
            return "" Try to extract text from binary docx (very simplified)
                    text_parts = []
        file_content = BytesIO()
        downloader = MediaIoBaseDownload(file_content, request)ignore')
                        for line in text.split('\n'):
        done = False        if len(line.strip()) > 10 and not line.startswith('<?xml'):
        while not done:         text_parts.append(line)
            _, done = downloader.next_chunk()_parts)
                    except:
        file_content.seek(0)rn "Text extraction failed - docx module not available"
            except Exception as e:
        # Extraer texto según el tipo de archivoe DOCX: {e}")
        if mime_type == "application/vnd.google-apps.document" or mime_type.endswith(".docx"):
            try:
                if docx:th PyPDF2 first
                    doc = docx.Document(file_content)
                    return "\n".join([para.text for para in doc.paragraphs])
                else:df = PdfFileReader(file_content)
                    # Simplified text extraction
                    content = file_content.read()NumPages()):
                    # Try to extract text from binary docx (very simplified)
                    text_parts = []
                    try:mportError:
                        text = content.decode('utf-8', errors='ignore') extraction
                        for line in text.split('\n'):
                            if len(line.strip()) > 10 and not line.startswith('<?xml'):
                                text_parts.append(line)errors='ignore')
                        return "\n".join(text_parts)
                    except:urn "PDF text extraction failed - no PDF library available"
                        return "Text extraction failed - docx module not available"
            except Exception as e:ayendo texto de PDF: {e}")
                print(f"Error extrayendo texto de DOCX: {e}")
        elif mime_type == "application/pdf":
            try:
                # Try with PyPDF2 first
                try:r al descargar archivo: {e}")
                    from pypdf2 import PdfFileReader
                    pdf = PdfFileReader(file_content)
                    text = ""t_name, sheet_names, job_description, top_n):
                    for page_num in range(pdf.getNumPages()):
                        text += pdf.getPage(page_num).extractText() + "\n"
                    return text
                except ImportError:, "Applicant", "Resume", "Information", "Interview link", "Phone Number", "E-mail", "Client", "idResume", "idInformation", "JOB DESCRIPTION"]
                    # If PyPDF2 isn't available, try a very simple text extraction
                    content = file_content.read()
                    try:n sheet_names:
                        return content.decode('utf-8', errors='ignore')
                    except:ent.open(spreadsheet_name).worksheet(sheet_name)
                        return "PDF text extraction failed - no PDF library available"
            except Exception as e:
                print(f"Error extrayendo texto de PDF: {e}")
                    continue  # Saltar hojas vacías
        return ""
                header_row = data[0]  # Primera fila con los encabezados
    except Exception as e:
        print(f"Error al descargar archivo: {e}")
        return ""vailable_headers = set(header_row)
                missing_headers = [h for h in expected_headers if h not in available_headers]
def get_candidates(spreadsheet_name, sheet_names, job_description, top_n):
    try:            print(f"Advertencia: La hoja '{sheet_name}' no tiene los encabezados: {missing_headers}")
        # Use the function without specifying a credentials file path
        client = authenticate_google_sheets()        
        
        # Handle special case for "arondb" (case-insensitive match)
        if spreadsheet_name.lower() == "arondb":        # Filtrar las filas de datos
            spreadsheet_name = "1EqsYq50pfSoZ5YM4AHKvqEUWT18CzCdgol6mWtRPTfU"# Omitir encabezados
            print(f"Converting 'arondb' to ID: {spreadsheet_name}")    if len(row) >= len(expected_headers):
        i in header_indices]
        expected_headers = ["Stage", "Applicant", "Resume", "Information", "Interview link", "Phone Number", "E-mail", "Client", "idResume", "idInformation", "JOB DESCRIPTION"](filtered_row)
        all_candidates = []pt Exception as sheet_error:
        r procesando la hoja {sheet_name}: {sheet_error}")
        for sheet_name in sheet_names:
            try:
                sheet = client.open(spreadsheet_name).worksheet(sheet_name)
                data = sheet.get_all_values()DataFrame(all_candidates, columns=expected_headers)
                
                if not data:
                    continue  # Saltar hojas vacías
                s disponibles en las hojas especificadas.")
                header_row = data[0]  # Primera fila con los encabezadosumber", "E-mail", "Client", "similarity"])
                
                # More flexible header checking
                available_headers = set(header_row)
                missing_headers = [h for h in expected_headers if h not in available_headers]me = df["idResume"] != ""
                if missing_headers:
                    print(f"Advertencia: La hoja '{sheet_name}' no tiene los encabezados: {missing_headers}")erate(df.data) 
                    continue] or has_info.data[i])])
                
                header_indices = [header_row.index(header) for header in expected_headers]
                
                # Filtrar las filas de datos
                for row in data[1:]:  # Omitir encabezadosd.DataFrame(columns=["Applicant", "Resume", "Information", "Interview link", "Phone Number", "E-mail", "Client", "similarity"])
                    if len(row) >= len(expected_headers):    return empty_df
                        filtered_row = [row[i] if i < len(row) else "" for i in header_indices]
                        all_candidates.append(filtered_row)
            except Exception as sheet_error:extracted_texts = []
                print(f"Error procesando la hoja {sheet_name}: {sheet_error}")ltered.data):
                continue_filtered.columns.index("idResume")]
        
        # Convertir a DataFrame
        df = pd.DataFrame(all_candidates, columns=expected_headers)ownload_file_from_drive(resume_id) if resume_id else ""
            info_text = download_file_from_drive(info_id) if info_id else ""
        # Verificar si hay candidatos
        if not all_candidates:ed_text)
            print("No hay candidatos disponibles en las hojas especificadas.")
            empty_df = pd.DataFrame(columns=["Applicant", "Resume", "Information", "Interview link", "Phone Number", "E-mail", "Client", "similarity"])
            return empty_df
        ined_text")
        # Filtrar candidatos que no tienen ni idResume ni idInformationfor i, text in enumerate(extracted_texts):
        has_resume = df["idResume"] != ""ed.data):
        has_info = df["idInformation"] != ""
        df_filtered = pd.DataFrame([row for i, row in enumerate(df.data) 
                                    if (has_resume.data[i] or has_info.data[i])])ilitud de coseno (mucho más ligero que sentence-transformers)
        df_filtered.columns = df.columnsvectorizer = TfidfVectorizer(stop_words='english')
        orm([job_description] + extracted_texts)
        if not df_filtered.data:
            print("No hay candidatos con resume o information.")del trabajo y cada candidato
            empty_df = pd.DataFrame(columns=["Applicant", "Resume", "Information", "Interview link", "Phone Number", "E-mail", "Client", "similarity"])
            return empty_df
        larities = cosine_similarity(job_vector, candidate_vectors)[0]
        # Extraer texto real de los archivos
        extracted_texts = []
        for i, row in enumerate(df_filtered.data):
            resume_id = row[df_filtered.columns.index("idResume")]
            info_id = row[df_filtered.columns.index("idInformation")]for i, sim in enumerate(similarities):
            
            resume_text = download_file_from_drive(resume_id) if resume_id else ""
            info_text = download_file_from_drive(info_id) if info_id else ""
            combined_text = resume_text + " " + info_text
            extracted_texts.append(combined_text)gest(top_n, "similarity")
         "Information", "Interview link", "Phone Number", "E-mail", "Client", "similarity"]
        # Add combined_text to df_filteredreturn top_candidates[result_columns]
        combined_idx = len(df_filtered.columns)
        df_filtered.columns.append("combined_text")
        for i, text in enumerate(extracted_texts):
            if i < len(df_filtered.data):import traceback
                df_filtered.data[i].append(text)
        
        # Usar TF-IDF y similitud de coseno (mucho más ligero que sentence-transformers)
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform([job_description] + extracted_texts)
        sheet ID
        # Calcular similitud entre la descripción del trabajo y cada candidato
        job_vector = tfidf_matrix[0:1]HKvqEUWT18CzCdgol6mWtRPTfU"
        candidate_vectors = tfidf_matrix[1:]: {spreadsheet_id}")
        similarities = cosine_similarity(job_vector, candidate_vectors)[0]
        
        # Add similarity to df_filtered
        similarity_idx = len(df_filtered.columns)first
        df_filtered.columns.append("similarity")
        for i, sim in enumerate(similarities):
            if i < len(df_filtered.data):
                df_filtered.data[i].append(sim)    print(f"Couldn't open by key, trying by name: {e}")
        .open(spreadsheet_id)
        # Get top candidates
        top_candidates = df_filtered.nlargest(top_n, "similarity")a hoja 'Candidates' ya existe
        result_columns = ["Applicant", "Resume", "Information", "Interview link", "Phone Number", "E-mail", "Client", "similarity"]et.worksheets()
        return top_candidates[result_columns]_names = [s.title for s in existing_sheets]
        
    except Exception as e:liminamos
        print(f"Error in get_candidates: {e}")if "Candidates" in sheet_names:
        import tracebackte. Eliminando...")
        traceback.print_exc()ksheet("Candidates")
        raise

def create_new_sheet(spreadsheet_id, results):ear nueva hoja 'Candidates'
    try:="Candidates", rows="100", cols="10")
        # Special case for known spreadsheet ID
        if spreadsheet_id == "ARONDB":
            spreadsheet_id = "1EqsYq50pfSoZ5YM4AHKvqEUWT18CzCdgol6mWtRPTfU"asattr(results, 'columns') and hasattr(results, 'data'):
            print(f"Using known spreadsheet ID: {spreadsheet_id}")
            lumns] + results.data
        client = authenticate_google_sheets()
        
        # Try to open by ID first            data = [list(results.columns)] + results.values.tolist()
        try:
            sheet = client.open_by_key(spreadsheet_id)put_option='RAW')
        except Exception as e:
            print(f"Couldn't open by key, trying by name: {e}")        # Retornar la URL de la nueva hoja
            sheet = client.open(spreadsheet_id)

        # Verificar si la hoja 'Candidates' ya existe
        existing_sheets = sheet.worksheets()
        sheet_names = [s.title for s in existing_sheets]
        traceback.print_exc()
        # Si la hoja 'Candidates' existe, la eliminamos
        if "Candidates" in sheet_names:
            print("La hoja 'Candidates' ya existe. Eliminando...")def get_all_sheets(spreadsheet_name_or_id):
            existing_sheet = sheet.worksheet("Candidates") un Google Sheets"""
            sheet.del_worksheet(existing_sheet)

        # Crear nueva hoja 'Candidates'
        new_sheet = sheet.add_worksheet(title="Candidates", rows="100", cols="10")preadsheet_name_or_id = "1EqsYq50pfSoZ5YM4AHKvqEUWT18CzCdgol6mWtRPTfU"
heet ID: {spreadsheet_name_or_id}")
        # Insertar los resultados
        if hasattr(results, 'columns') and hasattr(results, 'data'):tenticarse y obtener el cliente de gspread
            # Our custom DataFrame implementation
            data = [results.columns] + results.data        
        else:
            # Standard pandas DataFrame
            data = [list(results.columns)] + results.values.tolist()    sheet = client.open_by_key(spreadsheet_name_or_id)
            s e:
        new_sheet.append_rows(data, value_input_option='RAW')g by name: {e}")
nt.open(spreadsheet_name_or_id)
        # Retornar la URL de la nueva hoja
        return new_sheet.urlener las hojas
                sheets = sheet.worksheets()
    except Exception as e:
        print(f"Error creating new sheet: {e}")
        import tracebacksheet_names = [sheet.title for sheet in sheets]
        traceback.print_exc()
        raise

def get_all_sheets(spreadsheet_name_or_id):
    """Obtiene todas las hojas de un Google Sheets"""pt Exception as e:
    try:
        # Special case for known spreadsheet ID
        if spreadsheet_name_or_id == "ARONDB":traceback.print_exc()
            spreadsheet_name_or_id = "1EqsYq50pfSoZ5YM4AHKvqEUWT18CzCdgol6mWtRPTfU"
            print(f"Using known spreadsheet ID: {spreadsheet_name_or_id}")                # Autenticarse y obtener el cliente de gspread        client = authenticate_google_sheets()                # Try to open by ID first        try:            sheet = client.open_by_key(spreadsheet_name_or_id)        except Exception as e:            print(f"Couldn't open by key, trying by name: {e}")            sheet = client.open(spreadsheet_name_or_id)                # Obtener las hojas        sheets = sheet.worksheets()                # Obtener los nombres de las hojas        sheet_names = [sheet.title for sheet in sheets]        print(f"Found sheets: {sheet_names}")        return sheet_names        
    except Exception as e:
        print(f"Error al obtener las hojas: {e}")
        import traceback
        traceback.print_exc()
        return []
