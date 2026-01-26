import os
from core.utils import paths


def test_project_root_and_dirs_exist():
    # Basic dir checks
    assert paths.PROJECT_ROOT.exists(), f"PROJECT_ROOT not found: {paths.PROJECT_ROOT}"
    assert paths.CONFIG_DIR.exists(), f"CONFIG_DIR not found: {paths.CONFIG_DIR}"
    assert paths.SQL_DIR.exists(), f"SQL_DIR not found: {paths.SQL_DIR}"


def test_django_check_runs():
    # Try to run a light Django check to ensure settings import
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        import django
        django.setup()
        from django.core.management import call_command
        call_command('check', verbosity=0)
    except Exception as e:
        # Fail the test early with a clear message
        raise AssertionError(f"Django check failed: {e}")
