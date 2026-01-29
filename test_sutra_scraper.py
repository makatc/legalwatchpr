#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script para verificar el scraper SUTRA
============================================

Prueba la sincronización de medidas legislativas desde SUTRA.
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import Bill
from core.utils.sutra_sync import sync_sutra_bills, sync_specific_bills


def test_sutra_sync():
    """Prueba la sincronización SUTRA."""
    print("\n--- TEST SUTRA SCRAPER ---")
    
    # Contar bills antes
    initial_count = Bill.objects.count()
    print(f"📊 Bills en DB (antes): {initial_count}")
    
    # Sincronizar 3 medidas de prueba
    print("\n🔄 Sincronizando 3 medidas de la Cámara...")
    synced = sync_sutra_bills(limit=3, chamber='C', start_number=1000)
    
    # Contar bills después
    final_count = Bill.objects.count()
    print(f"\n📊 Bills en DB (después): {final_count}")
    print(f"✅ Nuevas medidas sincronizadas: {synced}")
    
    # Mostrar últimas medidas
    print("\n📋 Últimas 5 medidas en DB:")
    for bill in Bill.objects.all().order_by('-last_updated')[:5]:
        print(f"   - {bill.number}: {bill.title[:60]}...")
    
    # Probar sincronización específica
    print("\n🎯 Probando sincronización específica...")
    specific_ids = ["P. de la C. 1005", "P. del S. 500"]
    print(f"IDs a sincronizar: {specific_ids}")
    
    synced_specific = sync_specific_bills(specific_ids)
    print(f"✅ Medidas específicas sincronizadas: {synced_specific}")
    
    print("\n--- TEST COMPLETADO ---")


if __name__ == '__main__':
    try:
        test_sutra_sync()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
