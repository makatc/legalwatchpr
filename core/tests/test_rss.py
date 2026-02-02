import pytest
from core.models import NewsSource
from core.utils.rss_sync import sync_all_rss_sources
import traceback

# Mark tests to need DB
pytestmark = pytest.mark.django_db

def test_rss_sync(capsys):
    """
    Test de Sincronización RSS.
    Verifica que se pueden crear fuentes y sincronizar noticias.
    """
    with capsys.disabled():
        name = "El Nuevo Dia - Puerto Rico"
        url = "https://www.elnuevodia.com/rss/puerto-rico"
        defaults = {
            'url': url,
            'is_active': True,
            'icon_class': 'fas fa-newspaper'
        }

        try:
            source, created = NewsSource.objects.get_or_create(name=name, defaults=defaults)
            if created:
                print(f"✅ Fuente creada: {source.name} -> {source.url}")
            else:
                print(f"ℹ️ Fuente existente: {source.name} -> {source.url}")
        except Exception as e:
            pytest.fail(f"ERROR creando/obteniendo NewsSource: {e}")

        print("⏳ Ejecutando sincronización...")
        try:
            count = sync_all_rss_sources(max_entries=5)
            if count > 0:
                print(f"🎉 ÉXITO: Se descargaron {count} noticias.")
            else:
                print("⚠️ No se descargaron noticias nuevas (posiblemente ya existen).")
        except Exception as e:
            traceback.print_exc()
            pytest.fail(f"ERROR durante la sincronización: {e}")
