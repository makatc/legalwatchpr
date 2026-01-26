"""Utility helpers for core module."""
from .paths import *  # Re-export paths for convenience

__all__ = ['PROJECT_ROOT', 'CONFIG_DIR', 'SQL_DIR', 'SCRIPTS_DIR', 'TEMPLATES_DIR', 'STATIC_DIR', 'DATA_DIR', 'ensure_dirs_exist']
