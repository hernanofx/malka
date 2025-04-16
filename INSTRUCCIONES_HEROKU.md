# Guía para solucionar el problema de credenciales en Heroku

Este documento contiene instrucciones paso a paso para resolver el problema de "Credentials file not found: credenciales.json and failed to create temporary credentials" en tu aplicación Heroku.

## Preparación antes de desplegar

1. Asegúrate de que el archivo `credenciales.json` esté incluido en el repositorio:
   ```bash
   git add projectAron/credenciales.json
   ```

2. Verifica que `.gitignore` NO excluya archivos de credenciales (ya lo he modificado para ti)

3. Realiza un commit con los cambios que he implementado:
   ```bash
   git add .
   git commit -m "Mejoras en manejo de credenciales para Heroku"
   ```

4. Sube los cambios a GitHub:
   ```bash
   git push origin main
   ```

## Opciones para desplegar en Heroku

### OPCIÓN 1: Despliegue desde GitHub

1. Ve al dashboard de Heroku
2. Selecciona tu aplicación
3. Ve a la pestaña "Deploy"
4. Conecta con GitHub y selecciona tu repositorio
5. Despliega la rama que contiene los cambios

### OPCIÓN 2: Despliegue directo desde Git

```bash
git push heroku main
```

## IMPORTANTE: Configurar variables de entorno en Heroku

**Después del despliegue**, configura las variables de entorno en Heroku:

1. Ejecuta el script `heroku_setup.py` para configurar las credenciales:
   ```bash
   python heroku_setup.py --set --app candidates25-e1e3e768b6cf
   ```

   Si el script anterior falla, configura manualmente las credenciales:
   ```bash
   # Desde Windows (PowerShell):
   heroku config:set GOOGLE_CREDENTIALS="$(Get-Content -Raw projectAron/credenciales.json)" --app candidates25-e1e3e768b6cf
   
   # Desde macOS/Linux:
   heroku config:set GOOGLE_CREDENTIALS="$(cat projectAron/credenciales.json)" --app candidates25-e1e3e768b6cf
   ```

2. Reinicia la aplicación para aplicar los cambios:
   ```bash
   heroku restart --app candidates25-e1e3e768b6cf
   ```

## Verificación y depuración

1. Después de configurar las credenciales, ejecuta el script de depuración en Heroku:
   ```bash
   heroku run python -m projectAron.heroku_debug --app candidates25-e1e3e768b6cf
   ```

2. Verifica los logs para comprobar si el problema se ha resuelto:
   ```bash
   heroku logs --tail --app candidates25-e1e3e768b6cf
   ```

## Resumen de cambios implementados

1. **Mejorado el manejo de credenciales** en `codigoARON_simple.py` con información de depuración detallada y múltiples métodos de autenticación.

2. **Creado scripts de ayuda**:
   - `heroku_setup.py`: Para configurar y verificar credenciales en Heroku
   - `heroku_debug.py`: Para diagnosticar problemas en el entorno de Heroku

3. **Modificado archivos de configuración**:
   - MANIFEST.in: Para incluir explícitamente los archivos de credenciales
   - setup.py: Para garantizar que los archivos de datos se incluyan en el paquete
   - .gitignore: Para no excluir los archivos de credenciales

Si sigues estos pasos, deberías poder resolver el problema de credenciales en tu aplicación Heroku.