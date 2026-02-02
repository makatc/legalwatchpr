import pytest
from core.models import Article
from datetime import datetime, timedelta
# Mark all tests in this module to use the database
pytestmark = pytest.mark.django_db

from services import (
    evaluate_search_quality, 
    format_evaluation_report
)
from core.models import Article

def test_metrics_evaluation(capsys):
    """
    Ejecuta evaluaciones de calidad de búsqueda usando métricas de IR.
    Uses capsys to capture output if needed, but primarily runs to valid logic execution.
    """
    # Force stdout to show during test execution if -s is used, otherwise it is captured
    with capsys.disabled():
        print("=" * 80)
        print("📊 EVALUACIÓN DE MÉTRICAS DE BÚSQUEDA")
        print("=" * 80)

        # Verificar que hay artículos
        num_articles = Article.objects.count()
        print(f"\n📋 Artículos en base de datos: {num_articles}")

        if num_articles == 0:
            print("⚠️ No hay artículos en la BD — creando artículos de prueba para la evaluación...")
            # Crear fuente y artículos de prueba (mismo dataset que test_hybrid_search)
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
                Article.objects.get_or_create(
                    link=art_data['url'],
                    defaults={
                        'title': art_data['title'],
                        'snippet': art_data['snippet'],
                        'source': test_source,
                        'published_at': datetime.now() - timedelta(days=1),
                    }
                )
            num_articles = Article.objects.count()
            print(f"✅ Artículos creados: {num_articles}")

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
            pytest.skip("No se pudieron crear queries de prueba. Verifica los datos.")

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
                # We don't want to crash the whole test suite for one failure here if possible, 
                # but for a test file, we probably should fail. 
                # For now let's just assert False to mark as failed
                pytest.fail(f"Error evaluando método {method}: {e}")

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
