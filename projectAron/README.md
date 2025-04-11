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

1. Crear una aplicación en Heroku:
   ```
   heroku create tu-app-name
   ```

2. Configurar variables de entorno:
   ```
   heroku config:set SECRET_KEY=your_secret_key
   heroku config:set AUTHORIZED_USERS=user1@example.com,user2@example.com
   ```

3. Configurar las credenciales de Google:
   ```
   heroku config:set GOOGLE_CREDENTIALS=$(cat credenciales.json)
   heroku config:set GOOGLE_CLIENT_SECRETS=$(cat client_secrets.json)
   ```

4. Deploy a Heroku:
   ```
   git push heroku main
   ```

## Contribución

Si deseas contribuir a este proyecto, por favor:
1. Haz un fork del repositorio
2. Crea una rama para tu feature (`git checkout -b feature/amazing-feature`)
3. Haz commit de tus cambios (`git commit -m 'Add some amazing feature'`)
4. Push a la rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request
