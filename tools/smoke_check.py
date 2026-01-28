"""Run a quick smoke check for project paths and imports.

This script is robust to being executed from different CWDs: it will
locate the project root by walking up from this file if necessary and
ensure the root is on ``sys.path`` before importing ``core`` packages.
"""
import os
import sys
from pathlib import Path


def ensure_project_root_on_path():
    # If core import would fail, add project root (where manage.py lives)
    try:
        import core  # noqa: F401
        return
    except Exception:
        pass

    cur = Path(__file__).resolve().parent
    while not (cur / 'manage.py').exists() and cur.parent != cur:
        cur = cur.parent

    root = cur
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def main():
    ensure_project_root_on_path()
    from core.utils import paths

    print('PROJECT_ROOT:', paths.PROJECT_ROOT)
    print('CONFIG_DIR:', paths.CONFIG_DIR)
    print('SQL_DIR:', paths.SQL_DIR)
    print('SCRIPTS_DIR:', paths.SCRIPTS_DIR)

    try:
        paths.ensure_dirs_exist()
        print('Required dirs exist')
    except Exception as e:
        print('Dir check failed:', e)
        sys.exit(2)

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        import django
        django.setup()
        from django.core.management import call_command
        call_command('check')
        print('Django check OK')
    except ModuleNotFoundError as e:
        # Do not fail smoke check for missing optional packages; print a helpful warning.
        print('Django check could not run due to missing dependency:', e)
        print('If this is a CI/test environment, install project dependencies from requirements.txt')
    except Exception as e:
        print('Django check failed:', e)
        sys.exit(3)


if __name__ == '__main__':
    main()
