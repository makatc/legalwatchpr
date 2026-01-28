from django.core.management.base import BaseCommand
from django.db import connection
from core.utils import paths
import sys


class Command(BaseCommand):
    help = 'Execute SQL in sql/create_hnsw_index.sql to create the HNSW index for pgvector (requires pgvector extension).'

    def add_arguments(self, parser):
        parser.add_argument('--yes', action='store_true', help='Run without confirmation')

    def handle(self, *args, **options):
        sql_path = paths.SQL_DIR / 'create_hnsw_index.sql'
        if not sql_path.exists():
            self.stderr.write(f'ERROR: SQL file not found: {sql_path}')
            return

        if not options.get('yes'):
            confirm = input(f'About to execute SQL at {sql_path}. Continue? [y/N]: ').strip().lower()
            if confirm != 'y':
                self.stdout.write('Aborted by user')
                return

        sql = sql_path.read_text(encoding='utf-8')
        self.stdout.write('Executing SQL...')
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql)
            self.stdout.write(self.style.SUCCESS('HNSW index SQL executed successfully'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Failed to execute SQL: {e}'))
            sys.exit(2)
