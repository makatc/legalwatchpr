import os
import sys
import time
import django
from django.utils import timezone

# 1. Configurar entorno Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Article, NewsSource

# Importación segura de la búsqueda
try:
    from services.hybrid_search import search_documents
except ImportError:
    search_documents = None

print("\n--- 🧪 TEST DE AUTOMATIZACIÓN DE EMBEDDINGS (P1) ---")

# 2. Crear Fuente de Prueba
src, _ = NewsSource.objects.get_or_create(
    name="Test AutoEmbed Source", 
    defaults={'url': 'http://autoembed-test.com'}
)

# 3. Crear Artículo (El Signal debería interceptar esto)
# Generamos un ID único basado en el tiempo para evitar error de "Duplicate Link"
unique_id = int(time.time())
fake_link = f"http://test.com/noticia-{unique_id}"

print(f"1. Creando artículo simulado ({unique_id})...")

try:
    art = Article.objects.create(
        title="Aumento masivo de fraude cibernético en la banca",
        link=fake_link,  # <--- AHORA EL LINK ES ÚNICO
        snippet="Los expertos advierten sobre nuevas modalidades de phishing usando IA.",
        published_at=timezone.now(),
        source=src
    )

    # 4. Verificar Embedding
    print("2. Verificando si se generó el vector automáticamente...")

    # Recargamos el objeto desde la DB
    art.refresh_from_db()

    # Verificación robusta (compatible con numpy)
    if art.embedding is not None:
        dim = len(art.embedding)
        print(f"   ✅ ÉXITO: Vector generado. Dimensión: {dim}")
        
        # 5. Prueba de Búsqueda
        if search_documents:
            print("\n3. Probando búsqueda semántica ('robo identidad banco')...")
            # Pausa breve para consistencia de DB
            time.sleep(1) 
            results = search_documents("robo identidad banco", limit=5)
            
            found = any(r['id'] == art.id for r in results)
            if found:
                print("   ✅ ÉXITO: El sistema encontró la noticia por similitud semántica.")
            else:
                print("   ⚠️ AVISO: No se encontró en el Top 5 (Normal si hay pocos datos).")
    else:
        print("   ❌ FALLO: El campo 'embedding' sigue vacío (None).")

    # Limpieza final
    art.delete()
    print("\n--- TEST FINALIZADO ---")

except Exception as e:
    print(f"❌ Error inesperado: {e}")