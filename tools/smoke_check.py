"""Run a quick smoke check for project paths and imports."""
import os
import sys
from core.utils import paths


def main():
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
    except Exception as e:
        print('Django check failed:', e)
        sys.exit(3)


if __name__ == '__main__':
    main()
