# Aplicación de Búsqueda de Candidatos

Esta aplicación web permite encontrar candidatos adecuados para un puesto basándose en descripciones de trabajo y perfiles de candidatos utilizando técnicas de procesamiento de texto.

## Sobre la versión optimizada

Esta es una versión optimizada y ligera que:
- Usa scikit-learn en lugar de sentence-transformers y PyTorch
- Reemplaza PyMuPDF con PyPDF2 (más ligero)
- Procesa archivos en memoria para reducir el uso de disco
- Usa TF-IDF y similitud de coseno en lugar de embeddings neuronales

## Soluciones a errores comunes

### Error de credenciales no encontradas
Si encuentras un error como `FileNotFoundError: Credentials file not found: credenciales.json`:

1. Este error ocurre cuando la aplicación no puede encontrar las credenciales de Google
2. Asegúrate de que la variable de entorno `GOOGLE_CREDENTIALS` esté correctamente configurada:
   ```
   heroku config:set GOOGLE_CREDENTIALS="$(cat credenciales.json)"
   ```
3. Verifica que la variable de entorno se haya establecido correctamente:
   ```
   heroku config:get GOOGLE_CREDENTIALS
   ```
4. Si estás ejecutando localmente, crea un archivo `.env` con el contenido:
   ```
   GOOGLE_CREDENTIALS='{"type":"service_account","project_id":"...","private_key":"...",...}'
   ```

### Error de importación de Werkzeug
Si encuentras un error como `ImportError: cannot import name 'url_quote' from 'werkzeug.urls'`:

1. Este error se debe a incompatibilidades de versiones entre Flask y Werkzeug
2. La solución es fijar versiones específicas en el archivo requirements.txt:
   ```
   flask==2.0.1
   werkzeug==2.0.1
   ```

### Error de NumPy/Pandas
Si encuentras un error como `ValueError: numpy.dtype size changed, may indicate binary incompatibility`:

1. Este error se debe a incompatibilidades entre versiones de NumPy y Pandas
2. La solución es fijar versiones compatibles en requirements.txt:
   ```
   numpy==1.20.3
   pandas==1.3.3
   scikit-learn==0.24.2
   ```
3. En la versión más reciente, hemos implementado manejadores de errores para cuando faltan dependencias

## Estructura del Proyecto

```
Malka/
├── Procfile                    # Comando para iniciar la aplicación en Heroku
├── requirements.txt            # Dependencias del proyecto (versión ligera)
├── runtime.txt                 # Versión de Python para Heroku
├── projectAron/                # Directorio principal de la aplicación
│   ├── __init__.py             # Convierte projectAron en un paquete Python
│   ├── appServer.py            # Servidor Flask original
│   ├── appServer_simple.py     # Servidor Flask optimizado para Heroku
│   ├── codigoARONconIA.py      # Lógica original con IA avanzada
│   ├── codigoARON_simple.py    # Lógica simplificada para Heroku
│   ├── credenciales.json       # Credenciales para Google APIs
│   ├── static/                 # Archivos estáticos (CSS, JS)
│   │   └── style.css
│   └── templates/              # Plantillas HTML
│       ├── index.html          # Página principal
│       └── login.html          # Formulario de login
```

## Despliegue en Heroku

1. Asegúrate de estar en el directorio raíz del proyecto (Malka/):
   ```
   cd c:\Users\Hernan\Desktop\TRABAJO\Malka
   ```

2. Inicializa un repositorio Git (si aún no lo has hecho):
   ```
   git init
   ```

3. Agrega todos los archivos al repositorio:
   ```
   git add .
   git commit -m "Versión optimizada para Heroku"
   ```

4. Crea una aplicación en Heroku:
   ```
   heroku create tu-app-name
   ```

5. Configura variables de entorno:
   ```
   heroku config:set SECRET_KEY=your_secret_key
   heroku config:set AUTHORIZED_USERS=user1@example.com,user2@example.com
   heroku config:set GOOGLE_CREDENTIALS="$(cat credenciales.json)"
   ```

6. Verifica que las variables de entorno se hayan establecido correctamente:
   ```
   heroku config:get SECRET_KEY
   heroku config:get AUTHORIZED_USERS
   heroku config:get GOOGLE_CREDENTIALS
   ```

7. Especifica manualmente el buildpack de Python:
   ```
   heroku buildpacks:set heroku/python
   ```

8. Despliega la aplicación:
   ```
   git push heroku master
   ```
   o si tu rama principal es main:
   ```
   git push heroku main
   ```

9. Si necesitas solucionar problemas después del despliegue:
   ```
   heroku logs --tail
   ```

10. Actualizar la aplicación después de realizar cambios:
    ```
    git add .
    git commit -m "Mensaje de actualización"
    git push heroku master
    ```

11. Abre la aplicación:
    ```
    heroku open
    ```

## Desarrollo Local

1. Crea un entorno virtual e instala dependencias:
   ```
   python -m venv venv
   venv\Scripts\activate  # En Windows
   pip install -r requirements.txt
   ```

2. Ejecuta la aplicación:
   ```
   python -m projectAron.appServer_simple
   ```
