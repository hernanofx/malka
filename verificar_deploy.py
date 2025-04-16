#!/usr/bin/env python
"""
Script para preparar y verificar el despliegue a Heroku
"""
import os
import json
import shutil
import sys

def verificar_credenciales():
    """Verifica que el archivo de credenciales exista y sea válido"""
    creds_path = "projectAron/credenciales.json"
    
    print("\n=== Verificando archivo de credenciales ===")
    
    if not os.path.exists(creds_path):
        print(f"❌ ERROR: No se encontró {creds_path}")
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
            
        print(f"✅ Archivo de credenciales válido ({creds_path})")
        print(f"  - Project ID: {creds.get('project_id')}")
        print(f"  - Client Email: {creds.get('client_email')}")
        return True
    except json.JSONDecodeError:
        print(f"❌ ERROR: El archivo {creds_path} no es un JSON válido")
        return False
    except Exception as e:
        print(f"❌ ERROR al leer {creds_path}: {str(e)}")
        return False

def verificar_archivos_importantes():
    """Verifica que los archivos importantes para el despliegue existan"""
    archivos = [
        "Procfile",
        "requirements.txt",
        "runtime.txt",
        "setup.py",
        "MANIFEST.in",
        "projectAron/__init__.py",
        "projectAron/appServer_simple.py",
        "projectAron/codigoARON_simple.py",
        "projectAron/templates/index.html",
        "projectAron/templates/login.html",
        "projectAron/static/style.css"
    ]
    
    print("\n=== Verificando archivos importantes ===")
    
    todos_existen = True
    for archivo in archivos:
        if os.path.exists(archivo):
            print(f"✅ {archivo}")
        else:
            print(f"❌ {archivo} no encontrado")
            todos_existen = False
    
    return todos_existen

def generar_comando_heroku():
    """Genera el comando para configurar credenciales en Heroku"""
    print("\n=== Comandos para configurar Heroku ===")
    
    creds_path = "projectAron/credenciales.json"
    if os.path.exists(creds_path):
        print("Ejecuta estos comandos después de crear tu aplicación en Heroku:")
        
        print("\n# Configurar variables de entorno:")
        print("heroku config:set SECRET_KEY=\"$(openssl rand -hex 32)\"")
        
        # Generar comando para configurar GOOGLE_CREDENTIALS
        # Desde Windows con PowerShell:
        print("\n# Desde PowerShell (Windows):")
        print(f'heroku config:set GOOGLE_CREDENTIALS="$(Get-Content -Raw {creds_path})"')
        
        # Desde bash (macOS/Linux):
        print("\n# Desde bash (macOS/Linux):")
        print(f'heroku config:set GOOGLE_CREDENTIALS="$(cat {creds_path})"')
        
        print("\n# O configura manualmente desde la interfaz web de Heroku")
        
        print("\n# Verifica la configuración:")
        print("heroku config")
    else:
        print("No se puede generar el comando porque no se encuentra el archivo de credenciales")

def instrucciones_deploy():
    """Muestra instrucciones para el deploy"""
    print("\n=== Instrucciones para el Deploy ===")
    print("""
1. Crea un repositorio en GitHub y haz push de los cambios:
   git init
   git add .
   git commit -m "Versión optimizada para Heroku"
   git remote add origin https://github.com/tu-usuario/tu-repo.git
   git push -u origin main

2. Crea una nueva aplicación en Heroku:
   heroku create nombre-app
   
3. Configura las variables de entorno como se indicó anteriormente

4. Despliega desde GitHub:
   - Ve a la sección "Deploy" en el dashboard de Heroku
   - Conecta con GitHub y selecciona tu repositorio
   - Habilita despliegues automáticos o realiza un despliegue manual

5. Alternativamente, despliega directamente desde Git:
   git push heroku main
   
6. Verifica los logs:
   heroku logs --tail
""")

def main():
    """Función principal del script"""
    print("=== Preparando despliegue a Heroku ===")
    
    credenciales_ok = verificar_credenciales()
    archivos_ok = verificar_archivos_importantes()
    
    generar_comando_heroku()
    instrucciones_deploy()
    
    print("\n=== Resumen ===")
    if credenciales_ok and archivos_ok:
        print("✅ Todo parece estar listo para el despliegue")
    else:
        print("⚠️ Hay problemas que necesitan ser resueltos antes del despliegue")

if __name__ == "__main__":
    main()