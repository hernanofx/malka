# Versión ligera del código original para Heroku
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from google.oauth2.service_account import Credentials
import os
import tempfile
import requests
import fitz
import docx
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from io import BytesIO
import numpy as np

# El modelo se cargará bajo demanda
model = None

def load_model():
    """Carga el modelo solo cuando es necesario"""
    global model
    if model is None:
        try:
            # Intentamos importar sentence_transformers
            from sentence_transformers import SentenceTransformer
            # Usamos un modelo más pequeño
            model = SentenceTransformer('paraphrase-MiniLM-L3-v2')
            print("Modelo cargado correctamente")
        except ImportError:
            print("Error al cargar sentence_transformers, usando alternativa")
            # Alternativa: usar API remota o implementación más simple
            model = SimpleSimilarityModel()
    return model

class SimpleSimilarityModel:
    """Implementación simple de similitud como alternativa al modelo pesado"""
    def __init__(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.vectorizer = TfidfVectorizer(stop_words='english')
        
    def encode(self, texts, convert_to_tensor=False):
        """Codifica textos usando TF-IDF (mucho más ligero)"""
        if isinstance(texts, str):
            texts = [texts]
        vectors = self.vectorizer.fit_transform(texts).toarray()
        return vectors
    
    def pytorch_cos_sim(self, a, b):
        """Implementación simple de similitud de coseno"""
        from sklearn.metrics.pairwise import cosine_similarity
        if len(a.shape) == 1:
            a = a.reshape(1, -1)
        if len(b.shape) == 1:
            b = b.reshape(1, -1)
        return cosine_similarity(a, b)

# ... Resto de funciones exactamente igual que en codigoARONconIA.py ...

def get_candidates(spreadsheet_name, sheet_names, job_description, top_n):
    client = authenticate_google_sheets("credenciales.json")
    
    expected_headers = ["Stage", "Applicant", "Resume", "Information", "Interview link", "Phone Number", "E-mail", "Client", "idResume", "idInformation", "JOB DESCRIPTION"]
    all_candidates = []
    
    # ... código existente ...
    
    # Cargar modelo bajo demanda (solo cuando se necesite)
    model = load_model()
    
    # ... resto del código igual ...
