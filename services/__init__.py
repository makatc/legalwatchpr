"""Services package for LegalWatchPR.

This module exposes a small public surface and uses lazy imports so
that heavy submodules are only loaded when their attributes are first
accessed. This can reduce import-time overhead but does not by itself
prevent circular imports if submodules import from ``services`` instead
of importing directly from their sibling modules.
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


def __dir__() -> list[str]:
    return sorted(list(__all__))
