import os
import sys
from pathlib import Path

# Robustly locate project root (allow override via LW_PROJECT_ROOT)
_env_root = os.getenv('LW_PROJECT_ROOT')
if _env_root:
    ROOT = Path(_env_root).resolve()
else:
    cur = Path(__file__).resolve().parent
    while not (cur / 'manage.py').exists() and cur.parent != cur:
        cur = cur.parent
    ROOT = cur

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
