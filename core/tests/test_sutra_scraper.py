import pytest
from core.models import Bill
from core.utils.legislative import sync_bills_range, sync_specific_bills

# Mark tests to use database
pytestmark = pytest.mark.django_db

def test_sutra_sync(capsys):
    """
    Prueba la sincronización SUTRA (Integration Test).
    Requiere acceso a internet y al sitio de SUTRA.
    """
    # Disable capture to see output or just run logic
    with capsys.disabled():
        print("\n--- TEST SUTRA SCRAPER ---")
        
        # Contar bills antes
        initial_count = Bill.objects.count()
        print(f"📊 Bills en DB (antes): {initial_count}")
        
        # Sincronizar 3 medidas de prueba
        print("\n🔄 Sincronizando 3 medidas de la Cámara...")
        # New signature: chamber, start, limit
        synced = sync_bills_range(chamber='C', start=1000, limit=3)
        
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
