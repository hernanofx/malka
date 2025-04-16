#!/usr/bin/env python
"""
Script para configurar o verificar las credenciales de Google en Heroku
"""
import json
import os
import subprocess
import sys

def check_credentials_file():
    """Verificar si existe el archivo de credenciales y es válido"""
    creds_path = "projectAron/credenciales.json"
    
    if not os.path.exists(creds_path):
        print(f"❌ ERROR: No se encontró el archivo {creds_path}")
        return False
    
    try:
        with open(creds_path, 'r') as f:
            creds = json.load(f)
        
        # Verificar campos obligatorios
        required_fields = ["type", "project_id", "private_key", "client_email"]
        missing = [field for field in required_fields if field not in creds]
        
        if missing:
            print(f"❌ ERROR: Faltan campos requeridos en credenciales.json: {', '.join(missing)}")
            return False
        
        print(f"✅ Archivo de credenciales válido: {creds_path}")
        print(f"  - Project ID: {creds.get('project_id')}")
        print(f"  - Client Email: {creds.get('client_email')}")
        return True
    except json.JSONDecodeError:
        print(f"❌ ERROR: El archivo {creds_path} no es un JSON válido")
        return False
    except Exception as e:
        print(f"❌ ERROR al leer {creds_path}: {str(e)}")
        return False

def set_heroku_credentials(app_name=None):
    """Configurar credenciales en Heroku desde el archivo local"""
    creds_path = "projectAron/credenciales.json"
    
    if not os.path.exists(creds_path):
        print(f"❌ ERROR: No se encontró el archivo {creds_path}")
        return False
    
    try:
        with open(creds_path, 'r') as f:
            creds_content = f.read()
        
        # Validar que sea JSON válido
        json.loads(creds_content)
        
        # Establecer app_param para el comando de heroku
        app_param = f" --app {app_name}" if app_name else ""
        
        print(f"🔄 Configurando GOOGLE_CREDENTIALS en Heroku{' para ' + app_name if app_name else ''}...")
        
        # Escapar comillas y generar el comando
        creds_content_escaped = creds_content.replace('"', '\\"')
        heroku_command = f'heroku config:set GOOGLE_CREDENTIALS="{creds_content_escaped}"{app_param}'
        
        # Ejecutar el comando
        print("Ejecutando comando de Heroku...")
        result = subprocess.run(heroku_command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Credenciales configuradas correctamente en Heroku")
            return True
        else:
            print(f"❌ ERROR al configurar credenciales en Heroku: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ ERROR al configurar credenciales en Heroku: {str(e)}")
        return False

def check_heroku_credentials(app_name=None):
    """Verificar si las credenciales están configuradas en Heroku"""
    app_param = f" --app {app_name}" if app_name else ""
    
    try:
        print(f"🔄 Verificando GOOGLE_CREDENTIALS en Heroku{' para ' + app_name if app_name else ''}...")
        
        # Ejecutar el comando para obtener las variables de entorno
        heroku_command = f'heroku config:get GOOGLE_CREDENTIALS{app_param}'
        result = subprocess.run(heroku_command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            # Verificar que sea JSON válido
            try:
                creds = json.loads(result.stdout.strip())
                print("✅ GOOGLE_CREDENTIALS está configurado en Heroku y es un JSON válido")
                print(f"  - Project ID: {creds.get('project_id')}")
                print(f"  - Client Email: {creds.get('client_email')}")
                return True
            except json.JSONDecodeError:
                print("❌ GOOGLE_CREDENTIALS está configurado en Heroku pero NO es un JSON válido")
                return False
        else:
            print("❌ GOOGLE_CREDENTIALS NO está configurado en Heroku")
            return False
    except Exception as e:
        print(f"❌ ERROR al verificar credenciales en Heroku: {str(e)}")
        return False

def restart_heroku_app(app_name=None):
    """Reiniciar la aplicación en Heroku"""
    app_param = f" --app {app_name}" if app_name else ""
    
    try:
        print(f"🔄 Reiniciando aplicación en Heroku{' (' + app_name + ')' if app_name else ''}...")
        
        # Ejecutar el comando para reiniciar la aplicación
        heroku_command = f'heroku restart{app_param}'
        result = subprocess.run(heroku_command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Aplicación reiniciada correctamente")
            return True
        else:
            print(f"❌ ERROR al reiniciar la aplicación: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ ERROR al reiniciar la aplicación: {str(e)}")
        return False

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Configurar o verificar credenciales de Google en Heroku')
    parser.add_argument('--check', action='store_true', help='Verificar archivo de credenciales local')
    parser.add_argument('--set', action='store_true', help='Configurar GOOGLE_CREDENTIALS en Heroku')
    parser.add_argument('--verify', action='store_true', help='Verificar GOOGLE_CREDENTIALS en Heroku')
    parser.add_argument('--restart', action='store_true', help='Reiniciar la aplicación en Heroku')
    parser.add_argument('--app', help='Nombre de la aplicación Heroku (opcional)')
    
    args = parser.parse_args()
    
    # Si no se proporcionan argumentos, mostrar ayuda
    if not (args.check or args.set or args.verify or args.restart):
        parser.print_help()
        return
    
    # Verificar archivo de credenciales local
    if args.check:
        check_credentials_file()
    
    # Configurar GOOGLE_CREDENTIALS en Heroku
    if args.set:
        set_heroku_credentials(args.app)
    
    # Verificar GOOGLE_CREDENTIALS en Heroku
    if args.verify:
        check_heroku_credentials(args.app)
    
    # Reiniciar la aplicación en Heroku
    if args.restart:
        restart_heroku_app(args.app)

if __name__ == "__main__":
    main()