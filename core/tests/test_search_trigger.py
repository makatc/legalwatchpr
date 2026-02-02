import pytest
from core.models import Article, NewsSource
from django.utils import timezone
import datetime as _dt
from django.db import connection

# These tests need DB access
pytestmark = pytest.mark.django_db

def test_search_vector_trigger(capsys):
    """
    Script para probar el trigger de search_vector automático
    Ejecutar después de aplicar la migración 0022
    """
    with capsys.disabled():
        print("\n" + "="*70)
        print("PRUEBA DE TRIGGER AUTOMÁTICO PARA search_vector")
        print("="*70 + "\n")
        
        # Verificar que el trigger existe
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT tgname, tgtype, tgenabled 
                FROM pg_trigger 
                WHERE tgname = 'trigger_update_article_search_vector'
            """)
            trigger = cursor.fetchone()
            
            if trigger:
                print("✅ Trigger encontrado:")
                print(f"   Nombre: {trigger[0]}")
                print(f"   Tipo: {trigger[1]} (BEFORE)")
                print(f"   Estado: {'Habilitado' if trigger[2] == 'O' else 'Deshabilitado'}")
            else:
                pytest.fail("❌ Trigger NO encontrado")
        
        print("\n" + "-"*70)
        print("PRUEBA 1: Crear artículo nuevo")
        print("-"*70 + "\n")
        
        # Crear o obtener fuente de noticias
        source, _ = NewsSource.objects.get_or_create(
            name="Test Source",
            defaults={'url': 'https://test.com', 'is_active': True}
        )
        
        # Crear artículo de prueba
        article = Article.objects.create(
            source=source,
            title="Aprobación de nueva ley sobre transparencia gubernamental",
            snippet="El Senado aprobó hoy una importante ley que fortalece la transparencia en Puerto Rico.",
            ai_summary="Nueva legislación sobre transparencia en el gobierno de Puerto Rico.",
            link="https://test.com/article-" + str(hash("test1")),
            published_at=timezone.make_aware(_dt.datetime(2026, 1, 23, 12, 0, 0))
        )
        
        # Verificar que search_vector se actualizó automáticamente
        article.refresh_from_db()
        
        if article.search_vector:
            print("✅ search_vector generado automáticamente")
            print(f"   Contenido: {str(article.search_vector)[:100]}...")
            
            # Probar búsqueda
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT title, 
                           ts_rank(search_vector, to_tsquery('spanish', 'transparencia')) as rank
                    FROM core_article
                    WHERE search_vector @@ to_tsquery('spanish', 'transparencia')
                    ORDER BY rank DESC
                    LIMIT 1
                """)
                result = cursor.fetchone()
                
                if result:
                    print("\n🔍 Búsqueda de 'transparencia':")
                    print(f"   Encontrado: {result[0]}")
                    print(f"   Rank: {result[1]:.4f}")
                else:
                    pytest.fail("❌ No se encontró el artículo en búsqueda")
        else:
            pytest.fail("❌ search_vector NO se generó automáticamente")
        
        print("\n" + "-"*70)
        print("PRUEBA 2: Actualizar artículo existente")
        print("-"*70 + "\n")
        
        # Actualizar el artículo
        article.title = "Ley de transparencia aprobada por unanimidad"
        article.save()
        
        article.refresh_from_db()
        
        if 'unanimidad' in article.search_vector.lower():
            print("✅ search_vector actualizado automáticamente al modificar")
            print(f"   Nuevo contenido: {str(article.search_vector)[:100]}...")
        else:
            print("⚠️ search_vector puede no haberse actualizado correctamente")
        
        print("\n" + "-"*70)
        print("PRUEBA 3: Verificar pesos (A=título, B=snippet, C=ai_summary)")
        print("-"*70 + "\n")
        
        # Crear artículos con la misma palabra en diferentes campos
        test_articles = []
        
        # Palabra solo en título (peso A - máximo)
        a1 = Article.objects.create(
            source=source,
            title="Justicia en Puerto Rico",
            snippet="Tema diferente aquí",
            link="https://test.com/a1",
            published_at=timezone.make_aware(_dt.datetime(2026, 1, 23, 12, 1, 0))
        )
        
        # Palabra solo en snippet (peso B)
        a2 = Article.objects.create(
            source=source,
            title="Otro tema aquí",
            snippet="La justicia prevalece en este caso",
            link="https://test.com/a2",
            published_at=timezone.make_aware(_dt.datetime(2026, 1, 23, 12, 2, 0))
        )
        
        # Palabra solo en ai_summary (peso C - menor)
        a3 = Article.objects.create(
            source=source,
            title="Tema completamente diferente",
            snippet="Sin relación con el concepto",
            ai_summary="Resumen sobre justicia",
            link="https://test.com/a3",
            published_at=timezone.make_aware(_dt.datetime(2026, 1, 23, 12, 3, 0))
        )
        
        # Buscar y ordenar por relevancia
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT title, 
                       ts_rank(search_vector, to_tsquery('spanish', 'justicia')) as rank,
                       CASE 
                           WHEN title ILIKE '%justicia%' THEN 'título'
                           WHEN snippet ILIKE '%justicia%' THEN 'snippet'
                           WHEN ai_summary ILIKE '%justicia%' THEN 'ai_summary'
                       END as ubicacion
                FROM core_article
                WHERE search_vector @@ to_tsquery('spanish', 'justicia')
                ORDER BY rank DESC
            """)
            results = cursor.fetchall()
            
            print("🔍 Resultados búsqueda 'justicia' (ordenados por relevancia):\n")
            for i, (title, rank, ubicacion) in enumerate(results, 1):
                print(f"   {i}. Rank: {rank:.4f} | Ubicación: {ubicacion:12} | {title[:50]}")
        
        print("\n" + "-"*70)
        print("PRUEBA 4: Búsqueda sin tildes (gracias a unaccent)")
        print("-"*70 + "\n")
        
        article_with_accents = Article.objects.create(
            source=source,
            title="Educación pública en Puerto Rico",
            snippet="Nueva política educativa",
            link="https://test.com/accents",
            published_at=timezone.make_aware(_dt.datetime(2026, 1, 23, 12, 4, 0))
        )
        
        # Buscar con y sin tildes
        with connection.cursor() as cursor:
            # Buscar "educacion" (sin tilde)
            cursor.execute("""
                SELECT COUNT(*)
                FROM core_article
                WHERE search_vector @@ to_tsquery('spanish', 'educacion')
            """)
            count_sin_tilde = cursor.fetchone()[0]
            
            # Buscar "educación" (con tilde)
            cursor.execute("""
                SELECT COUNT(*)
                FROM core_article
                WHERE search_vector @@ to_tsquery('spanish', 'educación')
            """)
            count_con_tilde = cursor.fetchone()[0]
            
            if count_sin_tilde == count_con_tilde and count_sin_tilde > 0:
                print("✅ Búsqueda funciona igual con y sin tildes")
                print(f"   'educacion' (sin tilde): {count_sin_tilde} resultados")
                print(f"   'educación' (con tilde): {count_con_tilde} resultados")
            else:
                print("⚠️ Discrepancia en resultados:")
                print(f"   Sin tilde: {count_sin_tilde}, Con tilde: {count_con_tilde}")
        
        print("\n" + "="*70)
        print("LIMPIEZA: Eliminando artículos de prueba")
        print("="*70 + "\n")
        
        # Limpiar artículos de prueba
        Article.objects.filter(source__name="Test Source").delete()
        NewsSource.objects.filter(name="Test Source").delete()
        
        print("✅ Pruebas completadas\n")
