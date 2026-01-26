"""Services package for LegalWatchPR.

This module exposes a small public surface while avoiding heavy
aggregate imports at package import time to reduce circular import
issues. Attributes are imported lazily when accessed.
"""
from typing import Any

_NAME_TO_MODULE = {
    'EmbeddingGenerator': 'embedding_service',
    'RRF_K': 'hybrid_search',
    'get_search_stats': 'hybrid_search',
    'search_documents': 'hybrid_search',
    'search_keyword_only': 'hybrid_search',
    'search_semantic_only': 'hybrid_search',
    'LatencyTracker': 'metrics',
    'SearchMetrics': 'metrics',
    'evaluate_search_quality': 'metrics',
    'format_evaluation_report': 'metrics',
}

__all__ = list(_NAME_TO_MODULE.keys())


def __getattr__(name: str) -> Any:
    if name in _NAME_TO_MODULE:
        module_name = _NAME_TO_MODULE[name]
        module = __import__(f"services.{module_name}", fromlist=[name])
        return getattr(module, name)
    raise AttributeError(f"module 'services' has no attribute '{name}'")


def __dir__():
    return sorted(list(__all__))
