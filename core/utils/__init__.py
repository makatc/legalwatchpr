"""Utility helpers for core module."""
# Re-export path utilities
from .paths import *  # noqa: F401, F403

# Re-export all functions from the original utils module (now helpers)
from ..helpers import (  # noqa: F401
    normalize_text,
    generate_diff_html,
    analyze_legal_diff,
    check_sutra_status,
    fetch_latest_news,
    generate_ai_summary,
    analyze_bill_relevance,
)

__all__ = [
    # Path utilities
    'PROJECT_ROOT', 'CONFIG_DIR', 'SQL_DIR', 'SCRIPTS_DIR', 
    'TEMPLATES_DIR', 'STATIC_DIR', 'DATA_DIR', 'ensure_dirs_exist',
    # Helper functions
    'normalize_text', 'generate_diff_html', 'analyze_legal_diff',
    'check_sutra_status', 'fetch_latest_news', 'generate_ai_summary',
    'analyze_bill_relevance',
]
