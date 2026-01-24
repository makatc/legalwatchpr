"""
Servicios de negocio para LegalWatchPR
"""
from .embedding_service import EmbeddingGenerator
from .hybrid_search import (RRF_K, get_search_stats, search_documents,
                            search_keyword_only, search_semantic_only)
from .metrics import (LatencyTracker, SearchMetrics, evaluate_search_quality,
                      format_evaluation_report)

__all__ = [
    'EmbeddingGenerator',
    'search_documents',
    'search_semantic_only',
    'search_keyword_only',
    'get_search_stats',
    'RRF_K',
    'SearchMetrics',
    'LatencyTracker',
    'evaluate_search_quality',
    'format_evaluation_report'
]
