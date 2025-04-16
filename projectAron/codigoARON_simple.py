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
                vector = [0] * len(self.vocabulary_)
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
    """Download file from Google Drive and return its content as text"""
    try:
        # Get credentials following the same pattern as authenticate_google_sheets
        if os.environ.get('GOOGLE_CREDENTIALS'):
            print(f"Using env credentials to download file: {file_id}")
            json_creds = json.loads(os.environ.get('GOOGLE_CREDENTIALS'))
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(json_creds, scope)
        else:
            print(f"Using file credentials to download file: {file_id}")
            creds_file = "credenciales.json"
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
        
        # Build the service
        service = build('drive', 'v3', credentials=creds)
        
        # Get file metadata
        file_metadata = service.files().get(fileId=file_id).execute()
        mime_type = file_metadata.get("mimeType", "")
        
        # Initialize download request based on mime type
        request = None
        if mime_type == "application/vnd.google-apps.document":
            request = service.files().export_media(
                fileId=file_id, 
                mimeType="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        else:
            request = service.files().get_media(fileId=file_id)
        
        # Return empty if no valid request
        if not request:
            print(f"Could not create download request for file: {file_id}")
            return ""
        
        # Download the file content
        file_content = BytesIO()
        downloader = MediaIoBaseDownload(file_content, request)
        
        done = False
        while not done:
            _, done = downloader.next_chunk()
        
        file_content.seek(0)
        
        # Extract text based on mime type
        if mime_type == "application/vnd.google-apps.document" or mime_type.endswith(".docx"):
            try:
                if docx:
                    doc = docx.Document(file_content)
                    return "\n".join([para.text for para in doc.paragraphs])
                else:
                    # Simplified text extraction
                    content = file_content.read()
                    try:
                        text = content.decode('utf-8', errors='ignore')
                        text_parts = []
                        for line in text.split('\n'):
                            if len(line.strip()) > 10 and not line.startswith('<?xml'):
                                text_parts.append(line)
                        return "\n".join(text_parts)
                    except:
                        return "Text extraction failed - docx module not available"
            except Exception as e:
                print(f"Error extracting text from DOCX: {e}")
        elif mime_type == "application/pdf":
            try:
                # Try with PyPDF2 first
                try:
                    from pypdf2 import PdfFileReader
                    pdf = PdfFileReader(file_content)
                    text = ""
                    for page_num in range(pdf.getNumPages()):
                        text += pdf.getPage(page_num).extractText() + "\n"
                    return text
                except ImportError:
                    # If PyPDF2 isn't available, try a simple text extraction
                    content = file_content.read()
                    try:
                        return content.decode('utf-8', errors='ignore')
                    except:
                        return "PDF text extraction failed - no PDF library available"
            except Exception as e:
                print(f"Error extracting text from PDF: {e}")
        
        return ""
            
    except Exception as e:
        print(f"Error downloading file: {e}")
        import traceback
        traceback.print_exc()
        return ""

def get_candidates(spreadsheet_name, sheet_names, job_description, top_n):
    try:
        # Use the function without specifying a credentials file path
        client = authenticate_google_sheets()
        
        # Handle special case for "arondb" (case-insensitive match)
        if spreadsheet_name.lower() == "arondb":
            spreadsheet_name = "1EqsYq50pfSoZ5YM4AHKvqEUWT18CzCdgol6mWtRPTfU"
            print(f"Converting 'arondb' to ID: {spreadsheet_name}")
        
        expected_headers = ["Stage", "Applicant", "Resume", "Information", "Interview link", "Phone Number", "E-mail", "Client", "idResume", "idInformation", "JOB DESCRIPTION"]
        all_candidates = []
        
        for sheet_name in sheet_names:
            try:
                # Try to open the sheet
                sheet = client.open_by_key(spreadsheet_name).worksheet(sheet_name)
                data = sheet.get_all_values()
                
                if not data:
                    continue  # Skip empty sheets
                
                header_row = data[0]  # First row with headers
                
                # Flexible header checking
                available_headers = set(header_row)
                missing_headers = [h for h in expected_headers if h not in available_headers]
                if missing_headers:
                    print(f"Warning: Sheet '{sheet_name}' is missing headers: {missing_headers}")
                    continue
                
                # Get the column indices for each expected header
                header_indices = [header_row.index(header) for header in expected_headers]
                
                # Filter data rows
                for row in data[1:]:  # Skip headers
                    if len(row) >= len(expected_headers):
                        filtered_row = [row[i] if i < len(row) else "" for i in header_indices]
                        all_candidates.append(filtered_row)
            except Exception as sheet_error:
                print(f"Error processing sheet {sheet_name}: {sheet_error}")
                continue
                
        # Convert to DataFrame
        df = pd.DataFrame(all_candidates, columns=expected_headers)
        
        # Check if there are candidates
        if not all_candidates:
            print("No candidates available in the specified sheets.")
            empty_df = pd.DataFrame(columns=["Applicant", "Resume", "Information", "Interview link", "Phone Number", "E-mail", "Client", "similarity"])
            return empty_df
        
        # Filter candidates without resume or information
        has_resume = df["idResume"] != ""
        has_info = df["idInformation"] != ""
        df_filtered = pd.DataFrame([row for i, row in enumerate(df.data) 
                                    if (has_resume.data[i] or has_info.data[i])])
        df_filtered.columns = df.columns
        
        if not df_filtered.data:
            print("No candidates with resume or information.")
            empty_df = pd.DataFrame(columns=["Applicant", "Resume", "Information", "Interview link", "Phone Number", "E-mail", "Client", "similarity"])
            return empty_df
            
        # Extract text from files
        extracted_texts = []
        for i, row in enumerate(df_filtered.data):
            resume_id = row[df_filtered.columns.index("idResume")]
            info_id = row[df_filtered.columns.index("idInformation")]
            
            resume_text = download_file_from_drive(resume_id) if resume_id else ""
            info_text = download_file_from_drive(info_id) if info_id else ""
            combined_text = resume_text + " " + info_text
            extracted_texts.append(combined_text)
        
        # Add combined_text to df_filtered
        df_filtered.columns.append("combined_text")
        for i, text in enumerate(extracted_texts):
            if i < len(df_filtered.data):
                df_filtered.data[i].append(text)
        
        # Use TF-IDF and cosine similarity
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform([job_description] + extracted_texts)
        
        # Calculate similarity
        job_vector = tfidf_matrix[0:1]
        candidate_vectors = tfidf_matrix[1:]
        similarities = cosine_similarity(job_vector, candidate_vectors)[0]
        
        # Add similarity to df_filtered
        df_filtered.columns.append("similarity")
        for i, sim in enumerate(similarities):
            if i < len(df_filtered.data):
                df_filtered.data[i].append(sim)
                
        # Get top candidates
        top_candidates = df_filtered.nlargest(top_n, "similarity")
        result_columns = ["Applicant", "Resume", "Information", "Interview link", "Phone Number", "E-mail", "Client", "similarity"]
        return top_candidates[result_columns]
        
    except Exception as e:
        print(f"Error in get_candidates: {e}")
        import traceback
        traceback.print_exc()
        raise

def create_new_sheet(spreadsheet_id, results):
    try:
        # Special case for known spreadsheet name
        if spreadsheet_id.lower() == "arondb":
            spreadsheet_id = "1EqsYq50pfSoZ5YM4AHKvqEUWT18CzCdgol6mWtRPTfU"
            print(f"Using known spreadsheet ID: {spreadsheet_id}")
            
        client = authenticate_google_sheets()
        
        # Try to open by ID first
        try:
            sheet = client.open_by_key(spreadsheet_id)
        except Exception as e:
            print(f"Couldn't open by key, trying by name: {e}")
            sheet = client.open(spreadsheet_id)

        # Check if 'Candidates' sheet already exists
        existing_sheets = sheet.worksheets()
        sheet_names = [s.title for s in existing_sheets]

        # Delete existing Candidates sheet if it exists
        if "Candidates" in sheet_names:
            print("'Candidates' sheet already exists. Deleting...")
            existing_sheet = sheet.worksheet("Candidates")
            sheet.del_worksheet(existing_sheet)

        # Create new 'Candidates' sheet
        new_sheet = sheet.add_worksheet(title="Candidates", rows="100", cols="10")

        # Insert results
        if hasattr(results, 'columns') and hasattr(results, 'data'):
            # Custom DataFrame implementation
            data = [results.columns] + results.data
        else:
            # Standard pandas DataFrame
            data = [list(results.columns)] + results.values.tolist()
            
        new_sheet.append_rows(data, value_input_option='RAW')

        # Return the new sheet URL
        return new_sheet.url
        
    except Exception as e:
        print(f"Error creating new sheet: {e}")
        import traceback
        traceback.print_exc()
        raise

def get_all_sheets(spreadsheet_name_or_id):
    """Get all sheets from a Google Sheets document"""
    try:
        # Special case for known spreadsheet name
        if spreadsheet_name_or_id.lower() == "arondb":
            spreadsheet_name_or_id = "1EqsYq50pfSoZ5YM4AHKvqEUWT18CzCdgol6mWtRPTfU"
            print(f"Using known spreadsheet ID: {spreadsheet_name_or_id}")
        
        # Authenticate and get gspread client
        client = authenticate_google_sheets()
        
        # Try to open by ID first
        try:
            sheet = client.open_by_key(spreadsheet_name_or_id)
        except Exception as e:
            print(f"Couldn't open by key, trying by name: {e}")
            sheet = client.open(spreadsheet_name_or_id)
        
        # Get all worksheets
        sheets = sheet.worksheets()
        
        # Get sheet names
        sheet_names = [sheet.title for sheet in sheets]
        print(f"Found sheets: {sheet_names}")

        return sheet_names
        
    except Exception as e:
        print(f"Error getting sheets: {e}")
        import traceback
        traceback.print_exc()
        return []
