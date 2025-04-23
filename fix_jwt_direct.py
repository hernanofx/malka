#!/usr/bin/env python
"""
Fix JWT Direct - Corrige el problema 'Invalid JWT Signature' directamente en Heroku

Este script usa un enfoque directo para corregir el problema:
1. Extrae las credenciales directamente con 'heroku config:get'
2. Corrige los caracteres de escape en la clave privada
3. Actualiza la variable con 'heroku config:set'
4. Reinicia la aplicación

Uso:
python fix_jwt_direct.py candidates25-e1e3e768b6cf
"""

import sys
import os
import json
import subprocess
import tempfile
import traceback

def main():
    if len(sys.argv) < 2:
        print("Error: Debes especificar el nombre de la aplicación de Heroku")
        print("Uso: python fix_jwt_direct.py nombre-de-la-app")
        sys.exit(1)
    
    app_name = sys.argv[1]
    print(f"Intentando corregir el problema de JWT para: {app_name}")
    
    # Paso 1: Obtener la credencial actual
    print("\n1. Obteniendo GOOGLE_CREDENTIALS de Heroku...")
    get_cmd = f'heroku config:get GOOGLE_CREDENTIALS --app {app_name}'
    process = subprocess.run(get_cmd, shell=True, capture_output=True, text=True)
    
    if process.returncode != 0:
        print(f"Error al obtener GOOGLE_CREDENTIALS: {process.stderr}")
        sys.exit(1)
    
    creds_str = process.stdout.strip()
    if not creds_str:
        print("Error: GOOGLE_CREDENTIALS está vacía")
        sys.exit(1)
    
    print(f"✅ GOOGLE_CREDENTIALS obtenida ({len(creds_str)} caracteres)")
    
    # Paso 2: Corregir la credencial
    print("\n2. Corrigiendo el formato de las credenciales...")
    try:
        creds = json.loads(creds_str)
        print("✅ Credenciales parseadas correctamente como JSON")
        
        if 'private_key' not in creds:
            print("Error: Las credenciales no contienen 'private_key'")
            sys.exit(1)
        
        private_key = creds['private_key']
        
        # Verificar si necesita corrección
        if '\\n' in private_key and '\n' not in private_key:
            print("Corrigiendo escapes de saltos de línea en la clave privada...")
            private_key = private_key.replace('\\n', '\n')
            creds['private_key'] = private_key
            print("✅ Clave privada corregida")
        else:
            print("La clave privada parece estar correctamente formateada")
            print("¿Deseas continuar con la actualización de todos modos? (s/n)")
            response = input().strip().lower()
            if response != 's' and response != 'si':
                print("Operación cancelada")
                sys.exit(0)
        
        # Convertir de nuevo a string
        fixed_creds_str = json.dumps(creds)
        
    except json.JSONDecodeError:
        print("Error: GOOGLE_CREDENTIALS no es un JSON válido")
        sys.exit(1)
    except Exception as e:
        print(f"Error inesperado al procesar las credenciales: {e}")
        traceback.print_exc()
        sys.exit(1)
    
    # Paso 3: Guardar en un archivo temporal
    print("\n3. Guardando credenciales corregidas en archivo temporal...")
    fd, temp_path = tempfile.mkstemp(suffix='.json')
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(fixed_creds_str)
        print(f"✅ Credenciales guardadas en: {temp_path}")
    except Exception as e:
        print(f"Error al guardar archivo temporal: {e}")
        sys.exit(1)
    
    # Paso 4: Actualizar en Heroku usando el archivo
    print("\n4. Actualizando GOOGLE_CREDENTIALS en Heroku...")
    
    # Método 1: Usando comando directo con archivo temporal
    print("Método 1: Usando archivo temporal")
    set_cmd = f'heroku config:set GOOGLE_CREDENTIALS="$(cat {temp_path})" --app {app_name}'
    
    process = subprocess.run(set_cmd, shell=True, capture_output=True, text=True)
    
    if process.returncode != 0:
        print(f"⚠️ Advertencia: Error con Método 1: {process.stderr}")
        print("Intentando Método 2...")
        
        # Método 2: Usando el valor directamente (menos fiable con caracteres especiales)
        print("\nMétodo 2: Usando valor directo")
        # Escapar comillas para la shell
        escaped_creds = fixed_creds_str.replace('"', '\\"')
        set_cmd2 = f'heroku config:set GOOGLE_CREDENTIALS="{escaped_creds}" --app {app_name}'
        
        process2 = subprocess.run(set_cmd2, shell=True, capture_output=True, text=True)
        
        if process2.returncode != 0:
            print(f"Error con Método 2: {process2.stderr}")
            print("\nIntentando Método 3: Usando heroku CLI con JSON...")
            
            # Método 3: Usar formato JSON para heroku config:set
            json_cmd = json.dumps({"GOOGLE_CREDENTIALS": fixed_creds_str})
            set_cmd3 = f'echo {json_cmd} | heroku config:set --app {app_name}'
            
            process3 = subprocess.run(set_cmd3, shell=True, capture_output=True, text=True)
            
            if process3.returncode != 0:
                print(f"Error con todos los métodos: {process3.stderr}")
                print("\n❌ No se pudo actualizar la variable en Heroku")
                print("Intenta manualmente ejecutar:")
                print(f"heroku config:set GOOGLE_CREDENTIALS=\"$(cat {temp_path})\" --app {app_name}")
                sys.exit(1)
            else:
                print("✅ GOOGLE_CREDENTIALS actualizada con Método 3")
        else:
            print("✅ GOOGLE_CREDENTIALS actualizada con Método 2")
    else:
        print("✅ GOOGLE_CREDENTIALS actualizada con Método 1")
    
    # Paso 5: Eliminar el archivo temporal
    try:
        os.unlink(temp_path)
        print(f"✅ Archivo temporal eliminado: {temp_path}")
    except Exception as e:
        print(f"No se pudo eliminar archivo temporal: {e}")
    
    # Paso 6: Reiniciar la aplicación
    print("\n5. Reiniciando la aplicación...")
    restart_cmd = f'heroku restart --app {app_name}'
    process = subprocess.run(restart_cmd, shell=True, capture_output=True, text=True)
    
    if process.returncode != 0:
        print(f"Error al reiniciar la aplicación: {process.stderr}")
        sys.exit(1)
    
    print("✅ Aplicación reiniciada correctamente")
    
    # Paso 7: Mostrar mensaje de éxito
    print("\n✅ OPERACIÓN COMPLETADA")
    print("La corrección del problema de JWT ha sido aplicada.")
    print("Prueba ahora tu aplicación para verificar que funciona correctamente.")
    print(f"URL de tu aplicación: https://{app_name}.herokuapp.com")

if __name__ == "__main__":
    main()