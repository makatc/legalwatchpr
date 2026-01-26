"""
Script de Prueba: Búsqueda Híbrida
==================================

Prueba la funcionalidad de búsqueda híbrida creando artículos de prueba,
generando embeddings y ejecutando búsquedas.
"""

import os
import sys
import django
from pathlib import Path

# Configure Django: robust project-root detection (supports LW_PROJECT_ROOT)
_env_root = os.getenv('LW_PROJECT_ROOT')
if _env_root:
    _root = Path(_env_root).resolve()
else:
    _root = Path(__file__).resolve().parent
    while not (_root / 'manage.py').exists() and _root.parent != _root:
        _root = _root.parent

if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Article
from services import search_documents, search_semantic_only, search_keyword_only, get_search_stats
from services import EmbeddingGenerator
from datetime import datetime, timedelta
import random

print("=" * 80)
print("🧪 PRUEBAS DE BÚSQUEDA HÍBRIDA")
print("=" * 80)

# 1. Verificar estado actual
print("\n📊 Estado actual de la base de datos:")
stats = get_search_stats()
print(f"  Total de artículos: {stats['total_articles']}")
print(f"  Con embedding: {stats['articles_with_embedding']} ({stats['embedding_coverage']:.1f}%)")
print(f"  Con search_vector: {stats['articles_with_search_vector']} ({stats['search_vector_coverage']:.1f}%)")
print(f"  Completamente buscables: {stats['articles_searchable']}")

# 2. Crear artículos de prueba si no hay suficientes
if stats['total_articles'] < 5:
    print("\n📝 Creando artículos de prueba...")
    
    # Crear fuente de noticias de prueba
    from core.models import NewsSource
    test_source, _ = NewsSource.objects.get_or_create(
        name="Fuente de Prueba",
        defaults={'url': 'https://ejemplo.pr/feed', 'is_active': True}
    )
    
    test_articles = [
        {
            'title': 'Ley de Transparencia y Acceso a la Información Pública',
            'snippet': 'El Senado aprobó una nueva ley de transparencia que requiere a todas las agencias gubernamentales publicar sus presupuestos en línea. La medida busca combatir la corrupción y mejorar la rendición de cuentas.',
            'url': 'https://ejemplo.pr/transparencia-2026',
        },
        {
            'title': 'Proyecto de Ley sobre Educación Virtual en Puerto Rico',
            'snippet': 'La Cámara de Representantes considera legislación para regular la educación virtual. El proyecto establece estándares de calidad y accesibilidad para plataformas educativas en línea.',
            'url': 'https://ejemplo.pr/educacion-virtual',
        },
        {
            'title': 'Reforma al Código Penal: Nuevas Penas por Delitos Cibernéticos',
            'snippet': 'Se propone endurecer las penas para delitos de fraude electrónico y robo de identidad digital. La reforma incluye sanciones de hasta 15 años de prisión para casos graves de cibercrimen.',
            'url': 'https://ejemplo.pr/reforma-penal',
        },
        {
            'title': 'Cambios en la Ley de Salud Mental: Mayor Acceso a Servicios',
            'snippet': 'Nueva legislación amplía la cobertura de servicios de salud mental en el plan de salud gubernamental. Se crean centros comunitarios de atención psicológica en 10 municipios.',
            'url': 'https://ejemplo.pr/salud-mental',
        },
        {
            'title': 'Medida Ambiental: Prohibición de Plásticos de Un Solo Uso',
            'snippet': 'A partir de julio de 2026, entra en vigor la prohibición de plásticos desechables en comercios. La ley promueve el uso de materiales biodegradables y reutilizables para reducir la contaminación.',
            'url': 'https://ejemplo.pr/plasticos-prohibidos',
        },
    ]
    
    for art_data in test_articles:
        article, created = Article.objects.get_or_create(
            link=art_data['url'],
            defaults={
                'title': art_data['title'],
                'snippet': art_data['snippet'],
                'source': test_source,
                'published_at': datetime.now() - timedelta(days=random.randint(1, 30)),
            }
        )
        if created:
            print(f"  ✅ Creado: {article.title[:50]}...")
        else:
            print(f"  ⏭️  Ya existe: {article.title[:50]}...")
    
    print(f"\n✅ Total de artículos en BD: {Article.objects.count()}")

# 3. Generar embeddings para artículos sin ellos
articles_sin_embedding = Article.objects.filter(embedding__isnull=True).count()
if articles_sin_embedding > 0:
    print(f"\n🤖 Generando embeddings para {articles_sin_embedding} artículos...")
    
    generator = EmbeddingGenerator()
    for article in Article.objects.filter(embedding__isnull=True):
        try:
            # Construir texto
            text_parts = []
            if article.title:
                text_parts.append(f"Título: {article.title}")
            if article.snippet:
                text_parts.append(f"Contenido: {article.snippet}")
            if article.ai_summary:
                text_parts.append(f"Resumen: {article.ai_summary}")
            
            text = '\n\n'.join(text_parts)
            
            # Generar embedding
            embedding = generator.encode(text)
            article.embedding = embedding
            article.save(update_fields=['embedding'])
            
            print(f"  ✅ Embedding generado: {article.title[:50]}...")
        except Exception as e:
            print(f"  ❌ Error en artículo {article.id}: {e}")

# 4. Ejecutar pruebas de búsqueda
print("\n" + "=" * 80)
print("🔍 EJECUTANDO BÚSQUEDAS DE PRUEBA")
print("=" * 80)

queries = [
    "transparencia y corrupción",
    "educación",
    "delitos informáticos",
    "salud",
    "medio ambiente",
]

for query in queries:
    print(f"\n🔎 Query: '{query}'")
    print("-" * 80)
    
    try:
        # Búsqueda híbrida
        print("\n  📊 Búsqueda Híbrida (RRF):")
        results_hybrid = search_documents(query, limit=3)
        if results_hybrid:
            for i, result in enumerate(results_hybrid[:3], 1):
                print(f"    {i}. [{result['rrf_score']:.4f}] {result['title'][:60]}...")
                print(f"       Ranks: Semántica={result['semantic_rank']}, Léxica={result['keyword_rank']}")
        else:
            print("    Sin resultados")
        
        # Búsqueda semántica
        print("\n  🧠 Búsqueda Semántica:")
        results_semantic = search_semantic_only(query, limit=3)
        if results_semantic:
            for i, result in enumerate(results_semantic[:3], 1):
                similarity = result.get('similarity', 0)
                print(f"    {i}. [sim={similarity:.4f}] {result['title'][:60]}...")
        else:
            print("    Sin resultados")
        
        # Búsqueda léxica
        print("\n  📝 Búsqueda Léxica:")
        results_keyword = search_keyword_only(query, limit=3)
        if results_keyword:
            for i, result in enumerate(results_keyword[:3], 1):
                rank_score = result.get('rank_score', 0)
                print(f"    {i}. [rank={rank_score:.4f}] {result['title'][:60]}...")
        else:
            print("    Sin resultados")
        
    except Exception as e:
        print(f"  ❌ Error: {e}")

# 5. Estadísticas finales
print("\n" + "=" * 80)
print("📊 ESTADÍSTICAS FINALES")
print("=" * 80)

stats_final = get_search_stats()
print(f"Total de artículos: {stats_final['total_articles']}")
print(f"Con embedding: {stats_final['articles_with_embedding']} ({stats_final['embedding_coverage']:.1f}%)")
print(f"Con search_vector: {stats_final['articles_with_search_vector']} ({stats_final['search_vector_coverage']:.1f}%)")
print(f"Completamente buscables: {stats_final['articles_searchable']}")

print("\n" + "=" * 80)
print("✅ PRUEBAS COMPLETADAS")
print("=" * 80)
