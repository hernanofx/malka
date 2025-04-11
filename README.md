# Aplicación de Búsqueda de Candidatos

Esta aplicación web permite encontrar candidatos adecuados para un puesto basándose en descripciones de trabajo y perfiles de candidatos utilizando IA.

## Estructura del Proyecto

```
Malka/
├── Procfile                    # Comando para iniciar la aplicación en Heroku
├── requirements.txt            # Dependencias del proyecto
├── runtime.txt                 # Versión de Python para Heroku
├── setup.py                    # Configuración del paquete Python
├── MANIFEST.in                 # Archivos a incluir en el paquete
├── projectAron/                # Directorio principal de la aplicación
│   ├── __init__.py             # Convierte projectAron en un paquete Python
│   ├── appServer.py            # Servidor Flask
│   ├── codigoARONconIA.py      # Lógica de la aplicación
│   ├── credenciales.json       # Credenciales para Google APIs
│   ├── static/                 # Archivos estáticos (CSS, JS)
│   │   └── style.css
│   └── templates/              # Plantillas HTML
│       └── index.html
```

## Problema con el tamaño de la aplicación en Heroku

La aplicación utiliza bibliotecas de machine learning (sentence-transformers, torch) que son muy pesadas, lo que hace que el tamaño total supere el límite de 500MB que permite Heroku en su plan gratuito.

### Opciones para resolver el problema:

#### Opción 1: Usar Heroku-Buildpack-Apt para instalar dependencias
```
heroku buildpacks:add --index 1 heroku-community/apt
```
Crea un archivo `Aptfile` en la raíz con las dependencias necesarias.

#### Opción 2: Reducir el tamaño de las dependencias
Modifica `requirements.txt` para usar versiones más ligeras:
```
# Usa una versión más ligera de transformers
transformers==4.18.0
sentence-transformers==2.2.2

# Especifica solo CPU para PyTorch para reducir tamaño
https://download.pytorch.org/whl/cpu/torch-1.11.0%2Bcpu-cp39-cp39-linux_x86_64.whl
https://download.pytorch.org/whl/cpu/torchvision-0.12.0%2Bcpu-cp39-cp39-linux_x86_64.whl
```

#### Opción 3: Usar plataformas alternativas
- **Render**: Soporta aplicaciones más grandes
- **PythonAnywhere**: Buena para aplicaciones de Python
- **Google Cloud Run**: Permite contenedores Docker personalizados

## Despliegue en Heroku

1. Asegúrate de estar en el directorio raíz del proyecto (Malka/):
   ```
   cd c:\Users\Hernan\Desktop\TRABAJO\Malka
   ```

2. Inicializa un repositorio Git:
   ```
   git init
   ```

3. Agrega todos los archivos al repositorio:
   ```
   git add .
   git commit -m "Initial commit"
   ```

4. Crea una aplicación en Heroku:
   ```
   heroku create tu-app-name
   ```

5. Configura variables de entorno:
   ```
   heroku config:set SECRET_KEY=your_secret_key
   heroku config:set AUTHORIZED_USERS=user1@example.com,user2@example.com
   ```

6. Especifica manualmente el buildpack de Python:
   ```
   heroku buildpacks:set heroku/python
   ```

7. Despliega la aplicación:
   ```
   git push heroku master
   ```
   o si tu rama principal es main:
   ```
   git push heroku main
   ```

8. Para solucionar problemas, revisa los logs:
   ```
   heroku logs --tail
   ```

## Alternativa: Despliegue en Render.com

1. Crea una cuenta en Render.com
2. Selecciona "New Web Service"
3. Conecta tu repositorio de GitHub
4. Configura el servicio:
   - Runtime: Python 3.9
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn projectAron.appServer:app`
5. Configura las variables de entorno igual que en Heroku
6. Haz clic en "Create Web Service"

## Desarrollo Local

1. Crea un entorno virtual e instala dependencias:
   ```
   python -m venv venv
   venv\Scripts\activate  # En Windows
   pip install -r requirements.txt
   ```

2. Ejecuta la aplicación:
   ```
   python -m projectAron.appServer
   ```

## Solución para reducir el tamaño de la aplicación

Para hacer que la aplicación sea compatible con Heroku, podemos:

1. Usar modelos de embeddings más pequeños
2. Cargar modelos desde HuggingFace en tiempo de ejecución en lugar de instalarlos
3. Implementar un enfoque de API donde los cálculos pesados se realicen en otro servicio
