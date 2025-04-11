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
