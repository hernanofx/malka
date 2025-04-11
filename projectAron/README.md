# Candidate Finder Application

Esta aplicación web permite encontrar candidatos adecuados para un puesto basándose en descripciones de trabajo y perfiles de candidatos utilizando IA.

## Características

- Autenticación de usuarios
- Integración con Google Sheets
- Análisis de texto con IA para encontrar candidatos adecuados
- Exportación de resultados a Google Sheets

## Configuración Local

1. Clonar el repositorio:
   ```
   git clone https://github.com/tu-usuario/tu-repositorio.git
   cd tu-repositorio
   ```

2. Crear un entorno virtual e instalar dependencias:
   ```
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configurar credenciales:
   - Crear un proyecto en Google Cloud Platform
   - Habilitar Google Sheets API y Google Drive API
   - Crear credenciales de cuenta de servicio
   - Descargar el archivo JSON de credenciales y guardarlo como `credenciales.json`
   - Configurar credenciales OAuth 2.0 y guardarlas como `client_secrets.json`

4. Ejecutar la aplicación:
   ```
   flask run
   ```

## Deployment a Heroku

1. Asegúrate de tener los siguientes archivos en la raíz de tu proyecto:
   - `Procfile`: Contiene el comando para iniciar la aplicación
   - `requirements.txt`: Lista todas las dependencias
   - `runtime.txt` (opcional): Especifica la versión de Python

2. Instala Heroku CLI y loguéate:
   ```
   heroku login
   ```

3. Inicializa un repositorio Git si aún no lo has hecho:
   ```
   git init
   git add .
   git commit -m "Initial commit"
   ```

4. Crear una aplicación en Heroku:
   ```
   heroku create tu-app-name
   ```

5. Configurar variables de entorno:
   ```
   heroku config:set SECRET_KEY=your_secret_key
   heroku config:set AUTHORIZED_USERS=user1@example.com,user2@example.com
   ```

6. Configurar las credenciales de Google:
   ```
   heroku config:set GOOGLE_CREDENTIALS="$(cat credenciales.json)"
   heroku config:set GOOGLE_CLIENT_SECRETS="$(cat client_secrets.json)"
   ```

7. Deploy a Heroku:
   ```
   git push heroku main
   ```
   
   Si tu rama principal es "master" en lugar de "main", usa:
   ```
   git push heroku master
   ```

8. Verifica que la aplicación se haya inicializado correctamente:
   ```
   heroku logs --tail
   ```

## Solución de problemas comunes de Heroku

- **Error de detección de buildpack**: Asegúrate de tener un archivo `requirements.txt` válido en la raíz.
- **Error H10 (App crashed)**: Revisa los logs con `heroku logs --tail` para ver el error específico.
- **Error R10 (Boot timeout)**: Tu aplicación tarda demasiado en iniciar, revisa posibles bloqueos.

## Contribución

Si deseas contribuir a este proyecto, por favor:
1. Haz un fork del repositorio
2. Crea una rama para tu feature (`git checkout -b feature/amazing-feature`)
3. Haz commit de tus cambios (`git commit -m 'Add some amazing feature'`)
4. Push a la rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request
