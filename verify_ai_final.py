import os
import sys
import django
import google.generativeai as genai

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings

print("\n--- PRUEBA FINAL DE INTELIGENCIA ARTIFICIAL ---")
try:
    key = settings.GOOGLE_API_KEY
    if not key: raise ValueError("No Key Found")
    
    # Probamos el modelo EXACTO que pusimos en helpers.py
    model_name = 'gemini-2.0-flash'
    print(f"📡 Conectando con modelo: {model_name}...")
    
    genai.configure(api_key=key)
    model = genai.GenerativeModel(model_name)
    response = model.generate_content("Responde: SISTEMA LISTO")
    
    print(f"🤖 Respuesta de Gemini: {response.text.strip()}")
    print("✅ TAREA P0 COMPLETADA: Repositorio Estable e IA Conectada.")
    
except Exception as e:
    print(f"❌ FALLO: {e}")