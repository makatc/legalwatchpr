from django.core.management.base import BaseCommand
import importlib


class Command(BaseCommand):
    help = 'Run the project scheduler. This is a thin wrapper that imports core.scheduler and starts it. Use with care.'

    def add_arguments(self, parser):
        parser.add_argument('--run', action='store_true', help='Actually run the scheduler (default is dry-run)')

    def handle(self, *args, **options):
        try:
            scheduler_mod = importlib.import_module('core.scheduler')
        except Exception as e:
            self.stderr.write(f'Could not import core.scheduler: {e}')
            return

        if not options.get('run'):
            self.stdout.write('Imported core.scheduler — use --run to actually start it.')
            return

        # Call a `start()` function if present
        start_fn = getattr(scheduler_mod, 'start', None)
        if callable(start_fn):
            self.stdout.write('Starting scheduler...')
            start_fn()
            self.stdout.write(self.style.SUCCESS('Scheduler started (in-process)'))
        else:
            self.stderr.write('core.scheduler has no start() callable')
