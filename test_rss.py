#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import traceback

# Configuración de entorno Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
try:
    import django
    django.setup()
except Exception as e:
    print(f"ERROR: no se pudo inicializar Django: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    from core.models import NewsSource
except Exception as e:
    print(f"ERROR: no se pudo importar NewsSource desde core.models: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    from core.utils.rss_sync import sync_all_rss_sources
except Exception as e:
    print(f"ERROR: no se pudo importar sync_all_rss_sources: {e}")
    traceback.print_exc()
    sys.exit(1)

def main():
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
        print(f"ERROR creando/obteniendo NewsSource: {e}")
        traceback.print_exc()
        sys.exit(1)

    print("⏳ Ejecutando sincronización...")
    try:
        count = sync_all_rss_sources(max_entries=5)
        if count > 0:
            print(f"🎉 ÉXITO: Se descargaron {count} noticias.")
        else:
            print("⚠️ No se descargaron noticias nuevas (posiblemente ya existen).")
    except Exception as e:
        print(f"ERROR durante la sincronización: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
import os
import sys
import django

# Setup
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import NewsSource
from core.utils.rss_sync import sync_all_rss_sources

# 1. Crear Fuente de Prueba (Corregido: sin logo_url)
source, created = NewsSource.objects.get_or_create(
    name='El Nuevo Dia - Puerto Rico',
    defaults={
        'url': 'https://www.elnuevodia.com/rss/puerto-rico',
        'is_active': True,
        'icon_class': 'fas fa-newspaper'
    }
)

if created:
    print(f'? Fuente creada: {source.name}')
else:
    print(f'?? Fuente existente: {source.name}')

# 2. Ejecutar Sincronizaci�n
print('? Ejecutando sincronizaci�n...')
count = sync_all_rss_sources(max_entries=5)

if count > 0:
    print(f'?? �XITO: Se descargaron {count} noticias.')
else:
    print('?? No se descargaron noticias nuevas (quiz�s ya existen).')
