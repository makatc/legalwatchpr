"""
Script de Evaluación de Métricas de Búsqueda
============================================

Ejecuta evaluaciones de calidad de búsqueda usando métricas de IR.
"""

import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from services import (
    evaluate_search_quality, 
    format_evaluation_report,
    SearchMetrics
)
from core.models import Article

print("=" * 80)
print("📊 EVALUACIÓN DE MÉTRICAS DE BÚSQUEDA")
print("=" * 80)

# Verificar que hay artículos
num_articles = Article.objects.count()
print(f"\n📋 Artículos en base de datos: {num_articles}")

if num_articles == 0:
    print("❌ No hay artículos para evaluar. Ejecuta primero test_hybrid_search.py")
    sys.exit(1)

# Obtener algunos IDs de artículos para ground truth
all_articles = list(Article.objects.all().values('id', 'title', 'snippet'))

print(f"\n📝 Artículos disponibles:")
for i, art in enumerate(all_articles[:10], 1):
    print(f"  {i}. [{art['id']}] {art['title'][:60]}...")

# Crear queries de prueba con ground truth conocido
# Basado en los artículos de prueba creados anteriormente
test_queries = []

# Query 1: transparencia
transparencia_ids = {
    art['id'] for art in all_articles 
    if 'transparencia' in art['title'].lower() or 
       (art['snippet'] and 'transparencia' in art['snippet'].lower())
}
if transparencia_ids:
    test_queries.append({
        'query': 'transparencia y corrupción',
        'relevant_ids': transparencia_ids
    })

# Query 2: educación
educacion_ids = {
    art['id'] for art in all_articles 
    if 'educación' in art['title'].lower() or 'educacion' in art['title'].lower() or
       (art['snippet'] and ('educación' in art['snippet'].lower() or 'educacion' in art['snippet'].lower()))
}
if educacion_ids:
    test_queries.append({
        'query': 'educación',
        'relevant_ids': educacion_ids
    })

# Query 3: salud
salud_ids = {
    art['id'] for art in all_articles 
    if 'salud' in art['title'].lower() or 
       (art['snippet'] and 'salud' in art['snippet'].lower())
}
if salud_ids:
    test_queries.append({
        'query': 'salud mental',
        'relevant_ids': salud_ids
    })

# Query 4: delitos
delitos_ids = {
    art['id'] for art in all_articles 
    if any(term in art['title'].lower() for term in ['delito', 'penal', 'cibernético', 'cibernetico']) or
       (art['snippet'] and any(term in art['snippet'].lower() for term in ['delito', 'penal', 'cibernético', 'cibernetico']))
}
if delitos_ids:
    test_queries.append({
        'query': 'delitos informáticos',
        'relevant_ids': delitos_ids
    })

# Query 5: ambiente
ambiente_ids = {
    art['id'] for art in all_articles 
    if any(term in art['title'].lower() for term in ['ambiente', 'ambiental', 'plástico', 'plastico']) or
       (art['snippet'] and any(term in art['snippet'].lower() for term in ['ambiente', 'ambiental', 'plástico', 'plastico']))
}
if ambiente_ids:
    test_queries.append({
        'query': 'medio ambiente',
        'relevant_ids': ambiente_ids
    })

if not test_queries:
    print("\n⚠️  No se pudieron crear queries de prueba. Verifica los datos.")
    sys.exit(1)

print(f"\n✅ Queries de prueba creadas: {len(test_queries)}")
for i, q in enumerate(test_queries, 1):
    print(f"  {i}. '{q['query']}' → {len(q['relevant_ids'])} documentos relevantes")

# Evaluar cada método
print("\n" + "=" * 80)
print("🔍 EJECUTANDO EVALUACIONES")
print("=" * 80)

methods = ['hybrid', 'semantic', 'keyword']
k_values = [1, 3, 5, 10]

results = {}

for method in methods:
    print(f"\n{'=' * 80}")
    print(f"Evaluando método: {method.upper()}")
    print(f"{'=' * 80}")
    
    try:
        evaluation = evaluate_search_quality(
            test_queries=test_queries,
            method=method,
            k_values=k_values
        )
        
        results[method] = evaluation
        
        # Mostrar reporte
        report = format_evaluation_report(evaluation)
        print(report)
        
    except Exception as e:
        print(f"❌ Error evaluando {method}: {e}")
        import traceback
        traceback.print_exc()

# Comparación final
print("\n" + "=" * 80)
print("📊 COMPARACIÓN DE MÉTODOS")
print("=" * 80)

if results:
    print("\nPrecision@1:")
    for method, eval_data in results.items():
        p1 = eval_data['precision_at_k'].get(1, 0.0)
        print(f"  {method:10s}: {p1:.3f} ({p1*100:.1f}%)")
    
    print("\nMAP (Mean Average Precision):")
    for method, eval_data in results.items():
        map_score = eval_data['map']
        print(f"  {method:10s}: {map_score:.3f}")
    
    print("\nLatencia Media:")
    for method, eval_data in results.items():
        mean_lat = eval_data['latency_ms']['mean']
        status = "✅" if mean_lat < 200 else "⚠️"
        print(f"  {method:10s}: {mean_lat:6.1f} ms {status}")
    
    print("\nRecall:")
    for method, eval_data in results.items():
        recall = eval_data['recall']
        print(f"  {method:10s}: {recall:.3f} ({recall*100:.1f}%)")
    
    # Mejor método por métrica
    print("\n🏆 MEJORES MÉTODOS POR MÉTRICA:")
    
    best_p1 = max(results.items(), key=lambda x: x[1]['precision_at_k'].get(1, 0.0))
    print(f"  Precision@1: {best_p1[0]} ({best_p1[1]['precision_at_k'][1]:.1%})")
    
    best_recall = max(results.items(), key=lambda x: x[1]['recall'])
    print(f"  Recall:      {best_recall[0]} ({best_recall[1]['recall']:.1%})")
    
    best_latency = min(results.items(), key=lambda x: x[1]['latency_ms']['mean'])
    print(f"  Latencia:    {best_latency[0]} ({best_latency[1]['latency_ms']['mean']:.1f} ms)")
    
    best_map = max(results.items(), key=lambda x: x[1]['map'])
    print(f"  MAP:         {best_map[0]} ({best_map[1]['map']:.3f})")

print("\n" + "=" * 80)
print("✅ EVALUACIÓN COMPLETADA")
print("=" * 80)

# Recomendaciones
print("\n💡 RECOMENDACIONES:")
print("-" * 80)

if results:
    hybrid_eval = results.get('hybrid')
    if hybrid_eval:
        p1 = hybrid_eval['precision_at_k'].get(1, 0.0)
        lat = hybrid_eval['latency_ms']['mean']
        recall = hybrid_eval['recall']
        
        if p1 >= 0.95:
            print("✅ Precision@1 excelente para búsquedas legales específicas")
        else:
            print("⚠️  Considera ajustar pesos RRF o mejorar embeddings para mayor Precision@1")
        
        if lat < 200:
            print("✅ Latencia dentro del objetivo (<200ms)")
        else:
            print("❌ Latencia alta - considera:")
            print("   • Crear índice HNSW para embeddings")
            print("   • Optimizar parámetros de búsqueda")
            print("   • Reducir top_k_candidates en RRF")
        
        if recall >= 0.80:
            print("✅ Recall alto - el sistema encuentra la mayoría de documentos relevantes")
        else:
            print("⚠️  Recall bajo - el sistema puede estar perdiendo documentos relevantes")
            print("   • Aumentar top_k_candidates en búsqueda")
            print("   • Revisar calidad de embeddings")
            print("   • Verificar cobertura de search_vector")

print("\n" + "=" * 80)
