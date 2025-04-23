# Solución al problema "Invalid JWT Signature" en Heroku

## El problema

El error `google.auth.exceptions.RefreshError: ('invalid_grant: Invalid JWT Signature.', {'error': 'invalid_grant', 'error_description': 'Invalid JWT Signature.'})` ocurre cuando las credenciales de Google almacenadas en Heroku tienen un formato incorrecto, específicamente con los caracteres de salto de línea en la clave privada.

## Causa raíz

Cuando se configura la variable de entorno `GOOGLE_CREDENTIALS` en Heroku, los saltos de línea en la clave privada (`private_key`) se guardan como texto literal `\n` en lugar de saltos de línea reales. Esto hace que la firma JWT sea inválida cuando la aplicación intenta autenticarse con Google.

## Soluciones

### Opción 1: Usar el script automático `fix_jwt_direct.py`

Este script corrige automáticamente el problema conectándose a Heroku, extrayendo las credenciales, corrigiendo el formato y actualizando la variable de entorno.

1. **Ejecuta el script** proporcionando el nombre de tu aplicación en Heroku:

```bash
python fix_jwt_direct.py candidates25-e1e3e768b6cf
```

2. **Verifica** que la aplicación funcione correctamente después de que el script termine.

### Opción 2: Corregir manualmente los saltos de línea

Si prefieres hacerlo manualmente:

1. **Obtén las credenciales actuales**:
```bash
heroku config:get GOOGLE_CREDENTIALS --app candidates25-e1e3e768b6cf > creds.json
```

2. **Edita el archivo** con un editor de texto:
   - Abre `creds.json`
   - Busca la clave `private_key`
   - Reemplaza todas las ocurrencias de `\\n` por saltos de línea reales

3. **Actualiza la variable en Heroku**:
```bash
heroku config:set GOOGLE_CREDENTIALS="$(cat creds.json)" --app candidates25-e1e3e768b6cf
```

4. **Reinicia la aplicación**:
```bash
heroku restart --app candidates25-e1e3e768b6cf
```

### Opción 3: Usar el script `fix_heroku_jwt.py` en la carpeta projectAron

Este script implementa un enfoque alternativo mediante el API de configuración de Heroku:

```bash
python projectAron/fix_heroku_jwt.py --app candidates25-e1e3e768b6cf
```

## Prevención de problemas futuros

Para evitar que este problema ocurra de nuevo:

1. **Utiliza siempre el flag `--json`** cuando configures credenciales en Heroku:
```bash
heroku config:set GOOGLE_CREDENTIALS="$(cat credenciales.json)" --json --app tu-app-heroku
```

2. **Verifica el formato de la clave privada** antes de configurarla. La clave debe contener:
   - Los marcadores `-----BEGIN PRIVATE KEY-----` y `-----END PRIVATE KEY-----`
   - Saltos de línea reales, no secuencias de escape `\n`

3. **Actualiza tu código** para que maneje automáticamente este problema:
   - Usa la implementación mejorada de `authenticate_google_sheets()` en `codigoARON_simple.py`
   - Esta función detecta y corrige automáticamente problemas con los saltos de línea

## Cómo verificar si el problema está resuelto

1. **Reinicia tu aplicación**:
```bash
heroku restart --app candidates25-e1e3e768b6cf
```

2. **Accede a la aplicación** y verifica que ya no aparezca el error:
```
https://candidates25-e1e3e768b6cf.herokuapp.com/
```

3. **Revisa los logs** para confirmar que no hay errores de autenticación:
```bash
heroku logs --tail --app candidates25-e1e3e768b6cf
```

## Datos técnicos adicionales

- **Biblioteca afectada**: `google.oauth2.service_account`
- **Versión de Python en Heroku**: 3.9 (según los logs)
- **Archivo JSON esperado**: Debe ser un archivo de credenciales de cuenta de servicio de Google válido
- **Requisito crítico**: La clave privada (`private_key`) debe tener la firma en formato PEM correcto con saltos de línea reales

## Contacto

Si continúas teniendo problemas después de aplicar estas soluciones, puedes:

1. Consultar la documentación oficial de Google sobre [credenciales de cuenta de servicio](https://cloud.google.com/iam/docs/service-accounts)
2. Revisar la [documentación de Heroku sobre variables de entorno](https://devcenter.heroku.com/articles/config-vars)