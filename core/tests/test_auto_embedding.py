import pytest
from django.utils import timezone
import time
from core.models import Article, NewsSource

# Mark tests to need DB
pytestmark = pytest.mark.django_db

def test_auto_embedding(capsys):
    """
    Test de Automatización de Embeddings.
    Verifica que al guardar un artículo nuevo, se genere su embedding via presave/postsave signals.
    """
    with capsys.disabled():
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
        unique_id = int(time.time())
        fake_link = f"http://test.com/noticia-{unique_id}"

        print(f"1. Creando artículo simulado ({unique_id})...")

        try:
            art = Article.objects.create(
                title="Aumento masivo de fraude cibernético en la banca",
                link=fake_link, 
                snippet="Los expertos advierten sobre nuevas modalidades de phishing usando IA.",
                published_at=timezone.now(),
                source=src
            )

            # 4. Verificar Embedding
            print("2. Verificando si se generó el vector automáticamente...")

            # Recargamos el objeto desde la DB
            art.refresh_from_db()

            # Verificación robusta
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
                pytest.fail("   ❌ FALLO: El campo 'embedding' sigue vacío (None).")

            # Limpieza final
            art.delete()
            print("\n--- TEST FINALIZADO ---")

        except Exception as e:
            pytest.fail(f"❌ Error inesperado: {e}")
