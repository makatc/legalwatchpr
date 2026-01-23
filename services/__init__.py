"""
Servicios de negocio para LegalWatchPR
"""
from .embedding_service import EmbeddingGenerator
from .hybrid_search import (
    search_documents,
    search_semantic_only,
    search_keyword_only,
    get_search_stats,
    RRF_K
)
from .metrics import (
    SearchMetrics,
    LatencyTracker,
    evaluate_search_quality,
    format_evaluation_report
)

__all__ = ['EmbeddingGenerator']
