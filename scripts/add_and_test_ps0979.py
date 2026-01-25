import os
import sys

# Ensure project root is on sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

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
