import os
import sys
from pathlib import Path

# Robustly locate project root (allow override via LW_PROJECT_ROOT)
_env_root = os.getenv('LW_PROJECT_ROOT')
if _env_root:
    cur = Path(_env_root).resolve()
else:
    cur = Path(__file__).resolve().parent
while not (cur / 'manage.py').exists() and cur.parent != cur:
    cur = cur.parent
ROOT = cur

if not (ROOT / 'manage.py').exists():
    start_from = _env_root if _env_root else str(Path(__file__).resolve().parent)
    raise RuntimeError(
        f"Could not locate Django project root from {start_from!r}; "
        "expected to find 'manage.py' in or above this directory. "
        "Check the LW_PROJECT_ROOT environment variable and project layout."
    )

ROOT_STR = str(ROOT)
if ROOT_STR not in sys.path:
    sys.path.insert(0, ROOT_STR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from core.models import MonitoredMeasure
from core.scraper import LegisScraper

m, created = MonitoredMeasure.objects.get_or_create(sutra_id='PS0979')
if not created:
    m.is_active = True
    m.save()
print('PS0979 ensured (created=%s)' % created)

scraper = LegisScraper()
result = scraper.scrape_bill('PS0979')
print('scrape_bill(PS0979) =>', result)
