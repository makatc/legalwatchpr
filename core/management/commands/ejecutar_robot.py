import logging
import time

from django.core.management.base import BaseCommand

from core.models import Bill, MonitoredMeasure
from core.utils.legislative import sync_bill_to_db

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Ejecuta el robot para verificar y descargar medidas legislativas desde SUTRA."

    def add_arguments(self, parser):
        parser.add_argument(
            "--start-id",
            type=int,
            default=1,
            help="ID inicial de la medida a escanear (ej: 1 para PC1)",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=10,
            help="Cantidad de medidas consecutivas a escanear",
        )

    def handle(self, *args, **options):
        start_id = options["start_id"]
        count = options["count"]

        # 1. Limpieza inicial
        try:
            deleted, _ = Bill.objects.filter(title__icontains="Error 404").delete()
            if deleted:
                self.stdout.write(f"🧹 Limpieza: {deleted} entradas 404 eliminadas.")
        except Exception:
            pass

        # 2. Identificar medidas a procesar
        monitored_measures = list(
            MonitoredMeasure.objects.filter(is_active=True).values_list("sutra_id", flat=True)
        )
        
        measures_to_process = [("🎯", m) for m in monitored_measures]
        for i in range(start_id, start_id + count):
            m_id = f"PC{i}"
            if m_id not in monitored_measures:
                measures_to_process.append(("🔍", m_id))

        self.stdout.write(f"📋 Procesando {len(measures_to_process)} medidas...")
        self.stdout.write("-" * 50)

        results = {"success": 0, "skip": 0, "error": 0}

        for prefix, measure_id in measures_to_process:
            self.stdout.write(f"{prefix} Procesando: {measure_id}")
            
            try:
                bill, ai_called = sync_bill_to_db(measure_id)
                
                if bill:
                    self.stdout.write(f"  📄 {bill.title[:60]}...")
                    results["success"] += 1
                else:
                    self.stdout.write("  ⏭️ No encontrado o error.")
                    results["skip"] += 1
                
                # Pausa
                time.sleep(10 if ai_called else 1)
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ❌ Error: {e}"))
                results["error"] += 1
                time.sleep(1)

        self.stdout.write("-" * 50)
        self.stdout.write(self.style.SUCCESS(f"✅ Completado: {results['success']} OK, {results['skip']} saltados, {results['error']} errores."))
