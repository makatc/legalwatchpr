import os
import sys
import google.generativeai as genai
from dotenv import load_dotenv

# Cargar entorno
load_dotenv()
api_key = os.getenv('GOOGLE_API_KEY')

if not api_key or 'PEGAR_TU' in api_key:
    print('❌ ERROR: Edita el archivo .env y pon tu clave real de Google.')
    sys.exit(1)

genai.configure(api_key=api_key)

print('\n--- 🤖 MODELOS DISPONIBLES PARA TU CUENTA ---')
try:
    count = 0
    # Listar modelos que soporten generación de contenido
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f'✅ {m.name}')
            count += 1
    
    if count == 0:
        print('⚠️ No se encontraron modelos. Tu API Key podría no tener permisos o ser inválida.')
    else:
        print(f'\nTotal encontrados: {count}')
        print('--- PRUEBA DE FUEGO (usando gemini-1.5-flash) ---')
        try:
            # Probamos con el modelo más común
            model = genai.GenerativeModel('gemini-1.5-flash')
            res = model.generate_content('Di: SISTEMA OK')
            print(f'💬 Respuesta: {res.text.strip()}')
        except Exception as e:
            print(f'❌ Error probando modelo específico: {e}')
            print('   (Esto es normal si tu cuenta no tiene acceso a la versión 1.5 todavía, intenta con gemini-pro)')

except Exception as e:
    print(f'❌ Error fatal conectando: {e}')