"""
Comando de Django: Evaluar Calidad de Búsqueda
==============================================

Ejecuta evaluaciones de métricas de IR sobre el sistema de búsqueda.
"""

from django.core.management.base import BaseCommand

from core.models import Article
from services import evaluate_search_quality, format_evaluation_report


class Command(BaseCommand):
    help = 'Evalúa métricas de calidad de búsqueda (Precision@K, Recall, MAP, Latencia)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--method',
            type=str,
            default='all',
            choices=['hybrid', 'semantic', 'keyword', 'all'],
            help='Método de búsqueda a evaluar (default: all)',
        )
        parser.add_argument(
            '--queries-file',
            type=str,
            help='Archivo JSON con queries de prueba y ground truth',
        )
    
    def handle(self, *args, **options):
        method = options['method']
        queries_file = options['queries_file']
        
        self.stdout.write('=' * 80)
        self.stdout.write(self.style.HTTP_INFO('📊 EVALUACIÓN DE CALIDAD DE BÚSQUEDA'))
        self.stdout.write('=' * 80)
        
        # Verificar artículos
        num_articles = Article.objects.count()
        self.stdout.write(f'\n📋 Artículos en base de datos: {num_articles}')
        
        if num_articles == 0:
            self.stdout.write(self.style.ERROR('❌ No hay artículos para evaluar'))
            return
        
        # Cargar queries de prueba
        if queries_file:
            self.stdout.write(self.style.ERROR('❌ Carga desde archivo aún no implementada'))
            return
        
        # Crear queries de prueba básicas
        test_queries = self._create_test_queries()
        
        if not test_queries:
            self.stdout.write(self.style.WARNING('⚠️  No se pudieron crear queries de prueba'))
            return
        
        self.stdout.write(f'✅ Queries de prueba: {len(test_queries)}')
        
        # Evaluar métodos
        methods_to_eval = ['hybrid', 'semantic', 'keyword'] if method == 'all' else [method]
        
        results = {}
        for eval_method in methods_to_eval:
            self.stdout.write(f'\n{"=" * 80}')
            self.stdout.write(f'Evaluando: {eval_method.upper()}')
            self.stdout.write(f'{"=" * 80}')
            
            try:
                evaluation = evaluate_search_quality(
                    test_queries=test_queries,
                    method=eval_method,
                    k_values=[1, 3, 5, 10]
                )
                
                results[eval_method] = evaluation
                
                # Mostrar reporte
                report = format_evaluation_report(evaluation)
                self.stdout.write(report)
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Error: {e}'))
        
        # Comparación final si se evaluaron múltiples métodos
        if len(results) > 1:
            self._show_comparison(results)
    
    def _create_test_queries(self):
        """Crea queries de prueba automáticamente basadas en artículos existentes."""
        all_articles = list(Article.objects.all().values('id', 'title', 'snippet'))
        test_queries = []
        
        # Query patterns
        patterns = [
            (['transparencia', 'corrupción'], 'transparencia y corrupción'),
            (['educación', 'educacion'], 'educación'),
            (['salud'], 'salud mental'),
            (['delito', 'penal', 'cibernético', 'cibernetico'], 'delitos informáticos'),
            (['ambiente', 'ambiental', 'plástico', 'plastico'], 'medio ambiente'),
        ]
        
        for keywords, query_text in patterns:
            relevant_ids = {
                art['id'] for art in all_articles 
                if any(kw in art['title'].lower() for kw in keywords) or
                   (art['snippet'] and any(kw in art['snippet'].lower() for kw in keywords))
            }
            
            if relevant_ids:
                test_queries.append({
                    'query': query_text,
                    'relevant_ids': relevant_ids
                })
        
        return test_queries
    
    def _show_comparison(self, results):
        """Muestra comparación entre métodos."""
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write(self.style.HTTP_INFO('📊 COMPARACIÓN DE MÉTODOS'))
        self.stdout.write('=' * 80)
        
        # Precision@1
        self.stdout.write('\nPrecision@1:')
        for method, eval_data in results.items():
            p1 = eval_data['precision_at_k'].get(1, 0.0)
            status = '✅' if p1 >= 0.95 else '⚠️'
            self.stdout.write(f'  {method:10s}: {p1:.3f} ({p1*100:.1f}%) {status}')
        
        # Latencia
        self.stdout.write('\nLatencia Media:')
        for method, eval_data in results.items():
            mean_lat = eval_data['latency_ms']['mean']
            status = '✅' if mean_lat < 200 else '⚠️'
            self.stdout.write(f'  {method:10s}: {mean_lat:6.1f} ms {status}')
        
        # MAP
        self.stdout.write('\nMAP:')
        for method, eval_data in results.items():
            map_score = eval_data['map']
            self.stdout.write(f'  {method:10s}: {map_score:.3f}')
        
        # Mejor método
        self.stdout.write('\n🏆 MEJOR POR MÉTRICA:')
        best_p1 = max(results.items(), key=lambda x: x[1]['precision_at_k'].get(1, 0.0))
        self.stdout.write(f'  Precision@1: {best_p1[0]}')
        
        best_latency = min(results.items(), key=lambda x: x[1]['latency_ms']['mean'])
        self.stdout.write(f'  Latencia:    {best_latency[0]}')
        
        best_map = max(results.items(), key=lambda x: x[1]['map'])
        self.stdout.write(f'  MAP:         {best_map[0]}')
        
        self.stdout.write('\n' + '=' * 80)
