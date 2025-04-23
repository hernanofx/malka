#!/usr/bin/env python
"""
Script para solucionar problemas específicos de la firma JWT en las credenciales de Heroku
"""
import os
import json
import argparse
import subprocess
import traceback

def check_jwt_signature():
    """Verifica si hay problemas de firma JWT en las credenciales actuales"""
    print("\n=== Verificando problemas de firma JWT en GOOGLE_CREDENTIALS ===")
    
    # Obtener credenciales de la variable de entorno
    google_creds = os.environ.get('GOOGLE_CREDENTIALS')
    if not google_creds:
        print("❌ ERROR: GOOGLE_CREDENTIALS no está definida")
        return False
    
    try:
        # Intentar parsear el JSON
        json_creds = json.loads(google_creds)
        print("✅ GOOGLE_CREDENTIALS es un JSON válido")
        
        # Verificar que tenga los campos requeridos
        required_fields = ["type", "project_id", "private_key", "client_email"]
        missing = [field for field in required_fields if field not in json_creds]
        if missing:
            print(f"❌ ERROR: Faltan campos requeridos en GOOGLE_CREDENTIALS: {', '.join(missing)}")
            return False
        
        # Verificar si la clave privada tiene el formato correcto
        private_key = json_creds.get("private_key", "")
        if "-----BEGIN PRIVATE KEY-----" not in private_key or "-----END PRIVATE KEY-----" not in private_key:
            print("❌ ERROR: El formato de la clave privada es incorrecto")
            print("La clave privada debe contener '-----BEGIN PRIVATE KEY-----' y '-----END PRIVATE KEY-----'")
            return False
            
        # Verificar si hay escapes literales \n en lugar de saltos de línea reales
        if "\\n" in private_key and "\n" not in private_key:
            print("⚠️ ADVERTENCIA: La clave privada contiene '\\n' literales en lugar de saltos de línea reales")
            print("Este es probablemente el origen del error 'invalid_grant: Invalid JWT Signature'")
            return False
            
        # Si llegamos aquí, la clave privada parece estar bien formateada
        print("✅ El formato de la clave privada parece correcto")
        return True
            
    except json.JSONDecodeError as e:
        print(f"❌ ERROR: GOOGLE_CREDENTIALS no es un JSON válido: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR desconocido al verificar GOOGLE_CREDENTIALS: {e}")
        traceback.print_exc()
        return False

def fix_jwt_signature(app_name=None):
    """Corrige problemas de firma JWT en las credenciales de Google"""
    print("\n=== Corrigiendo problemas de firma JWT en GOOGLE_CREDENTIALS ===")
    
    # Obtener credenciales de la variable de entorno
    google_creds = os.environ.get('GOOGLE_CREDENTIALS')
    if not google_creds:
        print("❌ ERROR: GOOGLE_CREDENTIALS no está definida")
        return False
    
    try:
        # Intentar parsear el JSON
        json_creds = json.loads(google_creds)
        
        # Verificar si la clave privada necesita corrección
        if "private_key" in json_creds:
            private_key = json_creds["private_key"]
            corrected = False
            
            # Corregir \n literales
            if "\\n" in private_key and "\n" not in private_key:
                print("Reemplazando '\\n' literales por saltos de línea reales")
                private_key = private_key.replace("\\n", "\n")
                json_creds["private_key"] = private_key
                corrected = True
                
            # Si se hizo alguna corrección, actualizar en Heroku
            if corrected:
                # Convertir a JSON string para la variable de entorno
                corrected_creds = json.dumps(json_creds)
                
                # Parámetro de app para Heroku
                app_param = f" --app {app_name}" if app_name else ""
                
                print(f"Actualizando GOOGLE_CREDENTIALS en Heroku{' para ' + app_name if app_name else ''}...")
                
                # Preparar comando para Heroku
                # La clave privada contiene múltiples líneas, así que necesitamos escapes adicionales para el shell
                corrected_creds_escaped = corrected_creds.replace('"', '\\"')
                heroku_command = f'heroku config:set GOOGLE_CREDENTIALS="{corrected_creds_escaped}"{app_param}'
                
                print("Ejecutando comando en Heroku...")
                result = subprocess.run(heroku_command, shell=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("✅ GOOGLE_CREDENTIALS actualizada correctamente en Heroku")
                    print("Reiniciando la aplicación para aplicar cambios...")
                    
                    # Reiniciar la aplicación
                    restart_command = f"heroku restart{app_param}"
                    restart_result = subprocess.run(restart_command, shell=True, capture_output=True, text=True)
                    
                    if restart_result.returncode == 0:
                        print("✅ Aplicación reiniciada correctamente")
                        return True
                    else:
                        print(f"❌ Error al reiniciar la aplicación: {restart_result.stderr}")
                        return False
                else:
                    print(f"❌ Error al actualizar GOOGLE_CREDENTIALS: {result.stderr}")
                    return False
            else:
                print("✅ No se necesita corrección en la clave privada")
                return True
                
    except json.JSONDecodeError as e:
        print(f"❌ ERROR: GOOGLE_CREDENTIALS no es un JSON válido: {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR desconocido al corregir GOOGLE_CREDENTIALS: {e}")
        traceback.print_exc()
        return False

def get_current_credentials(app_name=None):
    """Obtiene las credenciales actuales de Heroku"""
    print("\n=== Obteniendo credenciales actuales de Heroku ===")
    
    # Parámetro de app para Heroku
    app_param = f" --app {app_name}" if app_name else ""
    
    try:
        # Obtener credenciales de Heroku
        heroku_command = f"heroku config:get GOOGLE_CREDENTIALS{app_param}"
        result = subprocess.run(heroku_command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            # Guardar en variable de entorno para facilitar procesamiento
            os.environ['GOOGLE_CREDENTIALS'] = result.stdout.strip()
            print(f"✅ Obtenidas GOOGLE_CREDENTIALS de Heroku{' para ' + app_name if app_name else ''}")
            print(f"   Longitud: {len(result.stdout.strip())} caracteres")
            return True
        else:
            print(f"❌ Error al obtener GOOGLE_CREDENTIALS de Heroku: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ ERROR al ejecutar comando de Heroku: {e}")
        traceback.print_exc()
        return False

def save_credentials_locally(output_file="heroku_creds.json", app_name=None):
    """Guarda las credenciales de Heroku en un archivo local para edición"""
    print(f"\n=== Guardando credenciales de Heroku en {output_file} ===")
    
    # Obtener credenciales actuales si no están disponibles
    if 'GOOGLE_CREDENTIALS' not in os.environ:
        if not get_current_credentials(app_name):
            return False
    
    google_creds = os.environ.get('GOOGLE_CREDENTIALS')
    
    try:
        # Guardar en archivo local
        with open(output_file, 'w') as f:
            # Intentar formatear como JSON para mejor legibilidad
            try:
                json_obj = json.loads(google_creds)
                json.dump(json_obj, f, indent=2)
            except:
                # Si falla, guardar como texto plano
                f.write(google_creds)
                
        print(f"✅ Credenciales guardadas en {output_file}")
        return True
    except Exception as e:
        print(f"❌ ERROR al guardar credenciales: {e}")
        return False

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Soluciona problemas de firma JWT en las credenciales de Google en Heroku')
    
    parser.add_argument('--check', action='store_true', 
                        help='Verificar problemas de firma JWT en las credenciales')
    
    parser.add_argument('--fix', action='store_true',
                        help='Corregir problemas de firma JWT automáticamente')
    
    parser.add_argument('--save', type=str, metavar='ARCHIVO',
                        help='Guardar credenciales en archivo local para edición manual')
    
    parser.add_argument('--app', type=str, 
                        help='Nombre de la aplicación de Heroku (opcional)')
    
    args = parser.parse_args()
    
    # Si no se especifican opciones, mostrar ayuda
    if not (args.check or args.fix or args.save):
        parser.print_help()
        return
    
    # Obtener credenciales actuales si es necesario
    if args.check or args.fix:
        if not get_current_credentials(args.app):
            print("No se pudieron obtener las credenciales actuales de Heroku")
            return
    
    # Verificar problemas
    if args.check:
        check_jwt_signature()
    
    # Corregir problemas
    if args.fix:
        fix_jwt_signature(args.app)
    
    # Guardar credenciales localmente
    if args.save:
        save_credentials_locally(args.save, args.app)

if __name__ == "__main__":
    main()