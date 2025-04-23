#!/usr/bin/env python
"""
Heroku JWT Fix - Corrige el problema de 'Invalid JWT Signature' en Heroku
automatizando el proceso de corrección de las credenciales de Google.

Este script:
1. Obtiene las credenciales actuales de Heroku
2. Corrige los caracteres de salto de línea (\\n → \n)
3. Actualiza las credenciales en Heroku
4. Reinicia la aplicación

Uso:
python fix_heroku_jwt.py --app nombre-de-tu-app
"""

import os
import json
import argparse
import subprocess
import traceback
import tempfile

def get_heroku_env(app_name):
    """Obtiene las variables de entorno de la aplicación Heroku"""
    print(f"Obteniendo variables de entorno para la app: {app_name}")
    
    cmd = f"heroku config --json --app {app_name}"
    process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if process.returncode != 0:
        print(f"Error al obtener variables de entorno: {process.stderr}")
        return None
        
    try:
        config_vars = json.loads(process.stdout)
        print(f"Variables de entorno obtenidas correctamente ({len(config_vars)} variables)")
        return config_vars
    except json.JSONDecodeError:
        print(f"Error al parsear la respuesta de Heroku: {process.stdout}")
        return None

def fix_credentials(creds_json):
    """Corrige los problemas de formato en las credenciales"""
    try:
        # Cargar el JSON de las credenciales
        creds = json.loads(creds_json)
        print("Credenciales cargadas correctamente como JSON")
        
        corrected = False
        
        # Verificar y corregir la clave privada
        if 'private_key' in creds:
            private_key = creds['private_key']
            
            # Corregir problema 1: saltos de línea escapados
            if '\\n' in private_key and '\n' not in private_key:
                print("Corrigiendo saltos de línea escapados (\\n → \\n)")
                private_key = private_key.replace('\\n', '\n')
                creds['private_key'] = private_key
                corrected = True
            
            # Verificar que tenga los marcadores BEGIN/END correctos
            if not ('-----BEGIN PRIVATE KEY-----' in private_key and '-----END PRIVATE KEY-----' in private_key):
                print("⚠️ ADVERTENCIA: La clave privada no tiene los marcadores BEGIN/END correctos")
        else:
            print("⚠️ ADVERTENCIA: Las credenciales no contienen 'private_key'")
        
        if corrected:
            print("✅ Credenciales corregidas")
            return json.dumps(creds)
        else:
            print("ℹ️ No se requirieron correcciones")
            return creds_json
            
    except json.JSONDecodeError:
        print("❌ Error: Las credenciales no son un JSON válido")
        return None
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        traceback.print_exc()
        return None

def update_heroku_env(app_name, var_name, var_value):
    """Actualiza una variable de entorno en Heroku"""
    print(f"Actualizando {var_name} en Heroku...")
    
    # Crear un archivo temporal con el valor
    fd, path = tempfile.mkstemp()
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(var_value)
        
        # Usar el archivo para establecer la variable (evita problemas con caracteres especiales)
        cmd = f'heroku config:set "{var_name}=$(cat {path})" --app {app_name}'
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if process.returncode != 0:
            print(f"❌ Error al actualizar variable: {process.stderr}")
            return False
        else:
            print(f"✅ Variable {var_name} actualizada correctamente")
            return True
    finally:
        os.unlink(path)  # Eliminar archivo temporal

def restart_heroku_app(app_name):
    """Reinicia la aplicación de Heroku"""
    print(f"Reiniciando la aplicación: {app_name}")
    cmd = f"heroku restart --app {app_name}"
    process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if process.returncode != 0:
        print(f"❌ Error al reiniciar la aplicación: {process.stderr}")
        return False
    else:
        print("✅ Aplicación reiniciada correctamente")
        return True

def apply_fix(app_name):
    """Proceso completo para corregir el problema de JWT"""
    print(f"\n=== Iniciando corrección de JWT para {app_name} ===\n")
    
    # 1. Obtener variables de entorno
    env_vars = get_heroku_env(app_name)
    if not env_vars:
        return False
    
    # 2. Verificar GOOGLE_CREDENTIALS
    if 'GOOGLE_CREDENTIALS' not in env_vars:
        print("❌ Error: GOOGLE_CREDENTIALS no está definida en la aplicación")
        return False
    
    # 3. Corregir credenciales
    fixed_creds = fix_credentials(env_vars['GOOGLE_CREDENTIALS'])
    if not fixed_creds:
        return False
    
    # 4. Actualizar en Heroku
    if not update_heroku_env(app_name, 'GOOGLE_CREDENTIALS', fixed_creds):
        return False
    
    # 5. Reiniciar la aplicación
    if not restart_heroku_app(app_name):
        return False
    
    print("\n=== Corrección completada exitosamente ===")
    print("Intenta acceder a tu aplicación ahora para verificar que el problema está resuelto.")
    return True

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Heroku JWT Fix - Corrige problemas de firma JWT en Heroku")
    parser.add_argument("--app", required=True, help="Nombre de la aplicación de Heroku")
    
    args = parser.parse_args()
    apply_fix(args.app)

if __name__ == "__main__":
    main()