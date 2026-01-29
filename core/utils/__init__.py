# Exponer funciones utilitarias para facilitar imports
from .paths import PROJECT_ROOT
from .rss_sync import sync_all_rss_sources

__all__ = [
    "PROJECT_ROOT",
    "sync_all_rss_sources",
]