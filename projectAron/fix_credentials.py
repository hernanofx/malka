"""
Script para ayudar a diagnosticar y corregir problemas de credenciales en Heroku
"""
import os
import json
import sys
import argparse

def fix_newlines_in_private_key(json_data):
    """
    Corrige los saltos de línea en la clave privada si están mal formateados
    """
    try:
        credentials = json.loads(json_data)
        if 'private_key' in credentials:
            # Reemplazar literales \n por saltos de línea reales
            private_key = credentials['private_key']
            if '\\n' in private_key and '\n' not in private_key:
                print("Encontrado '\\n' literal en private_key, reemplazando por saltos de línea reales")
                private_key = private_key.replace('\\n', '\n')
                credentials['private_key'] = private_key
                return json.dumps(credentials)
        return json_data
    except Exception as e:
        print(f"Error al procesar JSON: {e}")
        return json_data

def main():
    parser = argparse.ArgumentParser(description='Herramienta para diagnosticar y corregir problemas de credenciales de Google')
    
    parser.add_argument('--check', action='store_true', 
                        help='Verificar la variable GOOGLE_CREDENTIALS')
    
    parser.add_argument('--fix', action='store_true',
                        help='Intentar corregir problemas comunes en GOOGLE_CREDENTIALS')
    
    parser.add_argument('--set-from-file', type=str, metavar='FILEPATH',
                        help='Establecer GOOGLE_CREDENTIALS desde un archivo JSON')
    
    parser.add_argument('--save-to-file', type=str, metavar='FILEPATH',
                        help='Guardar GOOGLE_CREDENTIALS actual a un archivo para edición')
    
    args = parser.parse_args()
    
    # Si no se proporcionaron argumentos, mostrar ayuda
    if not (args.check or args.fix or args.set_from_file or args.save_to_file):
        parser.print_help()
        return
    
    # Verificar credenciales
    if args.check:
        print("== Verificando GOOGLE_CREDENTIALS ==")
        google_creds = os.environ.get('GOOGLE_CREDENTIALS')
        
        if not google_creds:
            print("❌ GOOGLE_CREDENTIALS no está definida")
            return
            
        print(f"✅ GOOGLE_CREDENTIALS tiene {len(google_creds)} caracteres")
        
        try:
            json_obj = json.loads(google_creds)
            print("✅ GOOGLE_CREDENTIALS contiene JSON válido")
            
            # Verificar campos requeridos
            required_keys = ["type", "project_id", "private_key", "client_email"]
            missing_keys = [key for key in required_keys if key not in json_obj]
            
            if missing_keys:
                print(f"❌ Faltan claves requeridas: {missing_keys}")
            else:
                print("✅ JSON contiene todas las claves requeridas")
                
            # Verificar tipo de credencial
            if json_obj.get("type") == "service_account":
                print("✅ Tipo de credencial: service_account")
            else:
                print(f"⚠️ Tipo de credencial inesperado: {json_obj.get('type')}")
                
            # Verificar formato de private_key
            if "private_key" in json_obj:
                private_key = json_obj["private_key"]
                if "-----BEGIN PRIVATE KEY-----" in private_key and "-----END PRIVATE KEY-----" in private_key:
                    print("✅ Formato de private_key válido")
                else:
                    print("❌ private_key parece estar mal formateada")
                    
                    if "\\n" in private_key and "\n" not in private_key:
                        print("  - private_key contiene '\\n' literales, debería contener saltos de línea reales")
                    if private_key.count("\\\\n") > 0:
                        print("  - private_key contiene '\\\\n' doblemente escapados")
        except json.JSONDecodeError as e:
            print(f"❌ GOOGLE_CREDENTIALS contiene JSON inválido: {e}")
            print(f"Primeros 100 caracteres: {google_creds[:100]}...")
    
    # Intentar corregir problemas comunes
    if args.fix:
        print("== Corrigiendo problemas comunes en GOOGLE_CREDENTIALS ==")
        google_creds = os.environ.get('GOOGLE_CREDENTIALS')
        
        if not google_creds:
            print("❌ GOOGLE_CREDENTIALS no está definida")
            return
            
        # Corregir saltos de línea en private_key
        fixed_creds = fix_newlines_in_private_key(google_creds)
        
        if fixed_creds != google_creds:
            print("✅ Se corrigieron problemas en GOOGLE_CREDENTIALS")
            print("Para aplicar los cambios, ejecuta:")
            print(f'heroku config:set GOOGLE_CREDENTIALS=\'{fixed_creds}\'')
        else:
            print("No se encontraron problemas para corregir automáticamente")
    
    # Establecer desde archivo
    if args.set_from_file:
        filepath = args.set_from_file
        if not os.path.exists(filepath):
            print(f"❌ El archivo {filepath} no existe")
            return
            
        try:
            with open(filepath, 'r') as f:
                content = f.read().strip()
                
            # Verificar que el contenido sea JSON válido
            json.loads(content)
            
            print(f"✅ Leyendo credenciales desde {filepath}")
            print("Para aplicar estas credenciales, ejecuta:")
            print(f'heroku config:set GOOGLE_CREDENTIALS=\'{content}\'')
        except json.JSONDecodeError as e:
            print(f"❌ El archivo no contiene JSON válido: {e}")
        except Exception as e:
            print(f"❌ Error al leer el archivo: {e}")
    
    # Guardar a archivo para edición
    if args.save_to_file:
        filepath = args.save_to_file
        google_creds = os.environ.get('GOOGLE_CREDENTIALS')
        
        if not google_creds:
            print("❌ GOOGLE_CREDENTIALS no está definida")
            return
            
        try:
            with open(filepath, 'w') as f:
                f.write(google_creds)
            print(f"✅ Credenciales guardadas en {filepath}")
            print("Después de editar el archivo, puedes actualizar la variable con:")
            print(f"heroku config:set GOOGLE_CREDENTIALS=\"$(cat {filepath})\"")
        except Exception as e:
            print(f"❌ Error al guardar a archivo: {e}")

if __name__ == "__main__":
    main()