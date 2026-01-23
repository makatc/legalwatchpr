"""
Servicio de Métricas para Búsqueda Híbrida
==========================================

Este módulo implementa métricas de evaluación para sistemas de recuperación
de información (Information Retrieval Evaluation).

Métricas implementadas:
- Precision@K: Precisión en los primeros K resultados
- Recall: Exhaustividad de la recuperación
- F1-Score: Media armónica de Precision y Recall
- Mean Reciprocal Rank (MRR): Posición del primer resultado relevante
- Average Precision (AP): Precisión promedio considerando orden
- Latency: Tiempo de respuesta de las consultas

Referencias:
- Manning et al., "Introduction to Information Retrieval"
- Relevance Judgments for Information Retrieval
"""

import time
import logging
from typing import List, Dict, Set, Any, Tuple, Optional
from collections import defaultdict
from statistics import mean, median
from services import search_documents, search_semantic_only, search_keyword_only

logger = logging.getLogger(__name__)


class SearchMetrics:
    """
    Calculador de métricas de evaluación para búsqueda.
    
    Permite evaluar la calidad de resultados comparando con un ground truth
    de documentos relevantes conocidos.
    """
    
    @staticmethod
    def precision_at_k(retrieved: List[int], relevant: Set[int], k: int) -> float:
        """
        Calcula Precision@K: proporción de documentos relevantes en los primeros K resultados.
        
        Precision@K = |{documentos relevantes} ∩ {primeros K recuperados}| / K
        
        Args:
            retrieved: Lista de IDs de documentos recuperados (en orden)
            relevant: Set de IDs de documentos relevantes (ground truth)
            k: Número de primeros resultados a considerar
            
        Returns:
            float: Precision@K entre 0.0 y 1.0
            
        Examples:
            >>> retrieved = [1, 2, 3, 4, 5]
            >>> relevant = {1, 3, 5}
            >>> SearchMetrics.precision_at_k(retrieved, relevant, k=5)
            0.6  # 3 de 5 son relevantes
        """
        if k <= 0:
            return 0.0
        
        top_k = retrieved[:k]
        relevant_in_top_k = sum(1 for doc_id in top_k if doc_id in relevant)
        
        return relevant_in_top_k / k
    
    @staticmethod
    def recall(retrieved: List[int], relevant: Set[int]) -> float:
        """
        Calcula Recall: proporción de documentos relevantes que fueron recuperados.
        
        Recall = |{documentos relevantes} ∩ {documentos recuperados}| / |{documentos relevantes}|
        
        Args:
            retrieved: Lista de IDs de documentos recuperados
            relevant: Set de IDs de documentos relevantes (ground truth)
            
        Returns:
            float: Recall entre 0.0 y 1.0
            
        Examples:
            >>> retrieved = [1, 2, 3]
            >>> relevant = {1, 3, 5, 7}
            >>> SearchMetrics.recall(retrieved, relevant)
            0.5  # 2 de 4 documentos relevantes fueron encontrados
        """
        if len(relevant) == 0:
            return 0.0
        
        relevant_retrieved = sum(1 for doc_id in retrieved if doc_id in relevant)
        
        return relevant_retrieved / len(relevant)
    
    @staticmethod
    def f1_score(precision: float, recall: float) -> float:
        """
        Calcula F1-Score: media armónica de Precision y Recall.
        
        F1 = 2 * (Precision * Recall) / (Precision + Recall)
        
        Args:
            precision: Valor de precisión (0.0 - 1.0)
            recall: Valor de recall (0.0 - 1.0)
            
        Returns:
            float: F1-Score entre 0.0 y 1.0
        """
        if precision + recall == 0:
            return 0.0
        
        return 2 * (precision * recall) / (precision + recall)
    
    @staticmethod
    def mean_reciprocal_rank(retrieved: List[int], relevant: Set[int]) -> float:
        """
        Calcula Mean Reciprocal Rank (MRR): inverso de la posición del primer resultado relevante.
        
        MRR mide qué tan rápido el sistema encuentra el primer documento relevante.
        Útil cuando el usuario busca UNA respuesta específica.
        
        Args:
            retrieved: Lista de IDs de documentos recuperados (en orden)
            relevant: Set de IDs de documentos relevantes
            
        Returns:
            float: MRR (0.0 si no hay relevantes, 1.0 si el primero es relevante)
            
        Examples:
            >>> retrieved = [10, 5, 3, 7]  # Primer relevante en posición 3
            >>> relevant = {3, 7}
            >>> SearchMetrics.mean_reciprocal_rank(retrieved, relevant)
            0.333...  # 1/3
        """
        for rank, doc_id in enumerate(retrieved, start=1):
            if doc_id in relevant:
                return 1.0 / rank
        
        return 0.0
    
    @staticmethod
    def average_precision(retrieved: List[int], relevant: Set[int]) -> float:
        """
        Calcula Average Precision (AP): promedio de precisiones en cada posición relevante.
        
        AP considera el orden de los resultados relevantes. Penaliza resultados
        relevantes que aparecen tarde.
        
        Args:
            retrieved: Lista de IDs de documentos recuperados (en orden)
            relevant: Set de IDs de documentos relevantes
            
        Returns:
            float: AP entre 0.0 y 1.0
            
        Examples:
            >>> retrieved = [1, 5, 3, 2, 4]
            >>> relevant = {1, 3, 4}
            >>> # Relevantes en posiciones 1, 3, 5
            >>> # Precision@1 = 1/1, Precision@3 = 2/3, Precision@5 = 3/5
            >>> # AP = (1.0 + 0.667 + 0.6) / 3 = 0.755
        """
        if len(relevant) == 0:
            return 0.0
        
        precisions = []
        relevant_count = 0
        
        for rank, doc_id in enumerate(retrieved, start=1):
            if doc_id in relevant:
                relevant_count += 1
                precision_at_rank = relevant_count / rank
                precisions.append(precision_at_rank)
        
        if len(precisions) == 0:
            return 0.0
        
        return sum(precisions) / len(relevant)
    
    @staticmethod
    def mean_average_precision(results: List[Tuple[List[int], Set[int]]]) -> float:
        """
        Calcula Mean Average Precision (MAP): promedio de AP sobre múltiples queries.
        
        MAP es una métrica estándar para evaluar sistemas de búsqueda.
        
        Args:
            results: Lista de tuplas (retrieved, relevant) para cada query
            
        Returns:
            float: MAP entre 0.0 y 1.0
        """
        if not results:
            return 0.0
        
        aps = [SearchMetrics.average_precision(retrieved, relevant) 
               for retrieved, relevant in results]
        
        return mean(aps) if aps else 0.0
    
    @staticmethod
    def ndcg_at_k(retrieved: List[int], relevant: Dict[int, float], k: int) -> float:
        """
        Calcula Normalized Discounted Cumulative Gain (NDCG@K).
        
        NDCG considera grados de relevancia (no solo binario relevante/irrelevante).
        Útil cuando hay documentos "muy relevantes" vs "algo relevantes".
        
        Args:
            retrieved: Lista de IDs de documentos recuperados (en orden)
            relevant: Dict de {doc_id: relevance_score} (scores más altos = más relevantes)
            k: Número de primeros resultados a considerar
            
        Returns:
            float: NDCG@K entre 0.0 y 1.0
        """
        if k <= 0 or not relevant:
            return 0.0
        
        # DCG (Discounted Cumulative Gain)
        dcg = 0.0
        for rank, doc_id in enumerate(retrieved[:k], start=1):
            rel = relevant.get(doc_id, 0.0)
            dcg += rel / (1.0 if rank == 1 else (rank ** 0.5))  # log2(rank+1) simplificado
        
        # IDCG (Ideal DCG): DCG si los documentos estuvieran ordenados perfectamente
        ideal_scores = sorted(relevant.values(), reverse=True)[:k]
        idcg = sum(rel / (1.0 if rank == 1 else (rank ** 0.5)) 
                   for rank, rel in enumerate(ideal_scores, start=1))
        
        if idcg == 0:
            return 0.0
        
        return dcg / idcg


class LatencyTracker:
    """
    Rastreador de latencia para consultas de búsqueda.
    
    Mide tiempos de respuesta y calcula estadísticas.
    """
    
    def __init__(self):
        self.latencies: List[float] = []
    
    def measure(self, func, *args, **kwargs) -> Tuple[Any, float]:
        """
        Mide el tiempo de ejecución de una función.
        
        Args:
            func: Función a ejecutar
            *args, **kwargs: Argumentos para la función
            
        Returns:
            Tuple[Any, float]: (resultado de la función, latencia en ms)
        """
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        
        latency_ms = (end - start) * 1000
        self.latencies.append(latency_ms)
        
        return result, latency_ms
    
    def get_stats(self) -> Dict[str, float]:
        """
        Obtiene estadísticas de latencia.
        
        Returns:
            Dict con mean, median, p95, p99, min, max en ms
        """
        if not self.latencies:
            return {
                'mean': 0.0,
                'median': 0.0,
                'p95': 0.0,
                'p99': 0.0,
                'min': 0.0,
                'max': 0.0,
                'count': 0
            }
        
        sorted_latencies = sorted(self.latencies)
        n = len(sorted_latencies)
        
        return {
            'mean': mean(self.latencies),
            'median': median(self.latencies),
            'p95': sorted_latencies[int(n * 0.95)] if n > 0 else 0.0,
            'p99': sorted_latencies[int(n * 0.99)] if n > 0 else 0.0,
            'min': min(self.latencies),
            'max': max(self.latencies),
            'count': n
        }
    
    def reset(self):
        """Reinicia las mediciones."""
        self.latencies = []


def evaluate_search_quality(
    test_queries: List[Dict[str, Any]],
    method: str = 'hybrid',
    k_values: List[int] = [1, 3, 5, 10]
) -> Dict[str, Any]:
    """
    Evalúa la calidad de búsqueda con un conjunto de queries de prueba.
    
    Args:
        test_queries: Lista de queries de prueba, cada una con:
            {
                'query': str,  # Texto de búsqueda
                'relevant_ids': Set[int]  # IDs de documentos relevantes
            }
        method: Método de búsqueda ('hybrid', 'semantic', 'keyword')
        k_values: Valores de K para Precision@K
        
    Returns:
        Dict con todas las métricas calculadas
        
    Examples:
        >>> test_queries = [
        ...     {
        ...         'query': 'ley de transparencia',
        ...         'relevant_ids': {1, 5, 10}
        ...     }
        ... ]
        >>> results = evaluate_search_quality(test_queries)
    """
    # Seleccionar función de búsqueda
    if method == 'semantic':
        search_func = search_semantic_only
    elif method == 'keyword':
        search_func = search_keyword_only
    else:  # hybrid
        search_func = search_documents
    
    # Rastreadores
    latency_tracker = LatencyTracker()
    all_results = []
    
    # Métricas agregadas
    precision_scores = defaultdict(list)
    recall_scores = []
    f1_scores = []
    mrr_scores = []
    ap_scores = []
    
    logger.info(f"Evaluando {len(test_queries)} queries con método '{method}'")
    
    for query_data in test_queries:
        query = query_data['query']
        relevant_ids = query_data['relevant_ids']
        
        # Ejecutar búsqueda con medición de latencia
        results, latency = latency_tracker.measure(
            search_func, 
            query, 
            limit=max(k_values) if k_values else 20
        )
        
        # Extraer IDs de resultados
        retrieved_ids = [r['id'] for r in results]
        
        # Calcular métricas
        for k in k_values:
            p_at_k = SearchMetrics.precision_at_k(retrieved_ids, relevant_ids, k)
            precision_scores[k].append(p_at_k)
        
        recall = SearchMetrics.recall(retrieved_ids, relevant_ids)
        recall_scores.append(recall)
        
        # F1 basado en Precision@max(k) y Recall
        max_k = max(k_values) if k_values else 10
        precision_for_f1 = SearchMetrics.precision_at_k(retrieved_ids, relevant_ids, max_k)
        f1 = SearchMetrics.f1_score(precision_for_f1, recall)
        f1_scores.append(f1)
        
        mrr = SearchMetrics.mean_reciprocal_rank(retrieved_ids, relevant_ids)
        mrr_scores.append(mrr)
        
        ap = SearchMetrics.average_precision(retrieved_ids, relevant_ids)
        ap_scores.append(ap)
        
        all_results.append((retrieved_ids, relevant_ids))
    
    # Calcular promedios
    map_score = SearchMetrics.mean_average_precision(all_results)
    latency_stats = latency_tracker.get_stats()
    
    evaluation = {
        'method': method,
        'num_queries': len(test_queries),
        'precision_at_k': {k: mean(scores) for k, scores in precision_scores.items()},
        'recall': mean(recall_scores) if recall_scores else 0.0,
        'f1_score': mean(f1_scores) if f1_scores else 0.0,
        'mrr': mean(mrr_scores) if mrr_scores else 0.0,
        'map': map_score,
        'latency_ms': latency_stats,
    }
    
    return evaluation


def format_evaluation_report(evaluation: Dict[str, Any]) -> str:
    """
    Formatea un reporte legible de evaluación.
    
    Args:
        evaluation: Diccionario de resultados de evaluate_search_quality
        
    Returns:
        str: Reporte formateado
    """
    report = []
    report.append("=" * 80)
    report.append(f"REPORTE DE EVALUACIÓN - Método: {evaluation['method'].upper()}")
    report.append("=" * 80)
    report.append(f"Queries evaluadas: {evaluation['num_queries']}")
    report.append("")
    
    report.append("📊 MÉTRICAS DE CALIDAD:")
    report.append("-" * 80)
    
    # Precision@K
    report.append("Precision@K:")
    for k, score in sorted(evaluation['precision_at_k'].items()):
        report.append(f"  P@{k:2d} = {score:.3f} ({score*100:.1f}%)")
    
    # Otras métricas
    report.append(f"\nRecall       = {evaluation['recall']:.3f} ({evaluation['recall']*100:.1f}%)")
    report.append(f"F1-Score     = {evaluation['f1_score']:.3f}")
    report.append(f"MRR          = {evaluation['mrr']:.3f}")
    report.append(f"MAP          = {evaluation['map']:.3f}")
    
    # Latencia
    report.append("")
    report.append("⚡ LATENCIA:")
    report.append("-" * 80)
    lat = evaluation['latency_ms']
    report.append(f"Media    = {lat['mean']:.1f} ms")
    report.append(f"Mediana  = {lat['median']:.1f} ms")
    report.append(f"P95      = {lat['p95']:.1f} ms")
    report.append(f"P99      = {lat['p99']:.1f} ms")
    report.append(f"Mín/Máx  = {lat['min']:.1f} / {lat['max']:.1f} ms")
    
    # Evaluación según objetivos
    report.append("")
    report.append("🎯 EVALUACIÓN vs OBJETIVOS:")
    report.append("-" * 80)
    
    # Objetivo: Precision@1 cercana al 100% para búsquedas legales
    p1 = evaluation['precision_at_k'].get(1, 0.0)
    if p1 >= 0.95:
        report.append(f"✅ Precision@1 = {p1:.1%} (objetivo: ≥95%)")
    elif p1 >= 0.80:
        report.append(f"⚠️  Precision@1 = {p1:.1%} (objetivo: ≥95%, mejorable)")
    else:
        report.append(f"❌ Precision@1 = {p1:.1%} (objetivo: ≥95%, CRÍTICO)")
    
    # Objetivo: Latencia < 200ms
    mean_lat = lat['mean']
    if mean_lat < 200:
        report.append(f"✅ Latencia media = {mean_lat:.1f} ms (objetivo: <200 ms)")
    else:
        report.append(f"❌ Latencia media = {mean_lat:.1f} ms (objetivo: <200 ms, LENTA)")
    
    report.append("=" * 80)
    
    return "\n".join(report)
