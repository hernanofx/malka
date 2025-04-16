#!/usr/bin/env python
"""
Script para configurar las credenciales de Google en Heroku
Ejecuta en tu entorno local para generar los comandos necesarios.
"""
import os
import json
import base64
import argparse

def generar_comando_heroku(creds_file, app_name=None):
    """
    Lee el archivo de credenciales y genera el comando para configurarlo en Heroku
    """
    try:
        # Leer el archivo de credenciales
        with open(creds_file, 'r') as f:
            creds_content = f.read().strip()
        
        # Intentar cargar como JSON para validar
        json.loads(creds_content)
        
        # Construir comando para Heroku
        app_param = f" --app {app_name}" if app_name else ""
        
        # Comando para PowerShell (Windows)
        print("=== Comando para PowerShell (Windows) ===")
        print(f'$env:CREDS=\'{creds_content}\'')
        print(f'heroku config:set GOOGLE_CREDENTIALS="$env:CREDS"{app_param}')
        
        # Comando para cmd (Windows)
        print("\n=== Comando para cmd (Windows) ===")
        print(f'set CREDS={creds_content}')
        print(f'heroku config:set GOOGLE_CREDENTIALS="%CREDS%"{app_param}')
        
        # Comando para bash (Linux/macOS)
        print("\n=== Comando para bash (Linux/macOS) ===")
        print(f'export CREDS=\'{creds_content}\'')
        print(f'heroku config:set GOOGLE_CREDENTIALS="$CREDS"{app_param}')
        
        # Alternativa con archivo temporal
        print("\n=== Alternativa con archivo temporal ===")
        print(f'heroku config:set GOOGLE_CREDENTIALS="$(cat {creds_file})"{app_param}')
        
        # Como verificar que se estableció correctamente
        print("\n=== Verificar la configuración ===")
        print(f'heroku config:get GOOGLE_CREDENTIALS{app_param}')
        
    except json.JSONDecodeError:
        print(f"ERROR: El archivo {creds_file} no contiene un JSON válido")
    except Exception as e:
        print(f"ERROR: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Genera comandos para configurar credenciales de Google en Heroku')
    parser.add_argument('--creds', '-c', default='projectAron/credenciales.json',
                        help='Ruta al archivo de credenciales (default: projectAron/credenciales.json)')
    parser.add_argument('--app', '-a', help='Nombre de la aplicación Heroku (opcional)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.creds):
        print(f"ERROR: No se encuentra el archivo {args.creds}")
        return
    
    generar_comando_heroku(args.creds, args.app)

if __name__ == "__main__":
    main()