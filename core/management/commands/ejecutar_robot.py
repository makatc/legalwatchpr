import time
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Bill, MonitoredMeasure
from core.scraper import LegisScraper
from core.utils import analyze_bill_relevance

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Ejecuta el robot para verificar y descargar medidas legislativas desde SUTRA."

    def add_arguments(self, parser):
        parser.add_argument(
            '--start-id',
            type=int,
            default=1,
            help='ID inicial de la medida a escanear (ej: 1 para PC1)'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Cantidad de medidas consecutivas a escanear'
        )

    def handle(self, *args, **options):
        start_id = options['start_id']
        count = options['count']
        
        # Cleanup any previous bad saves with 'Error 404' in title
        try:
            deleted, _ = Bill.objects.filter(title__icontains="Error 404").delete()
            if deleted:
                self.stdout.write(f"🧹 Limpieza: eliminadas {deleted} entradas con 'Error 404' en el título.")
        except Exception as e:
            logger.warning("Cleanup failed: %s", e)

        # Check if there are any monitored measures
        monitored_count = MonitoredMeasure.objects.filter(is_active=True).count()
        
        if monitored_count == 0:
            self.stdout.write("⚠️ No hay medidas en seguimiento. Agregue una desde el Dashboard para comenzar.")
            self.stdout.write(f"Iniciando escaneo secuencial desde PC{start_id} hasta PC{start_id + count - 1}...")
        else:
            self.stdout.write(f"✓ {monitored_count} medidas en seguimiento activo.")

        # Initialize scraper
        scraper = LegisScraper()
        
        # Get monitored measure IDs (if any)
        monitored_measures = list(
            MonitoredMeasure.objects.filter(is_active=True).values_list('sutra_id', flat=True)
        )

        # Build list of IDs to process: monitored first, then sequential scan
        measures_to_process = []
        
        # Add monitored measures
        for measure_id in monitored_measures:
            measures_to_process.append(('monitored', measure_id))
        
        # Add sequential scan range
        for i in range(start_id, start_id + count):
            measure_id = f"PC{i}"
            if measure_id not in monitored_measures:
                measures_to_process.append(('sequential', measure_id))

        self.stdout.write(f"📋 Total de medidas a procesar: {len(measures_to_process)}")
        self.stdout.write("-" * 80)

        success_count = 0
        skip_count = 0
        error_count = 0

        for scan_type, measure_id in measures_to_process:
            prefix = "🎯" if scan_type == 'monitored' else "🔍"
            self.stdout.write(f"{prefix} Procesando: {measure_id}")

            try:
                # Scrape bill data directly - let scraper handle URL validation
                bill_data = scraper.scrape_bill(measure_id)
                
                # If scraper returns None (404 or failure), skip saving
                if bill_data is None:
                    self.stdout.write(f"  ⏭️  No se encontraron datos válidos para {measure_id}")
                    skip_count += 1
                    time.sleep(1)
                    continue

                # Extract and validate scraped data
                bill_number = bill_data.get('number') or measure_id
                bill_title = bill_data.get('title') or f"Proyecto de la Cámara {measure_id}"
                
                self.stdout.write(f"  📄 Título: {bill_title[:60]}...")

                # Persist to database (only fields present in Bill model)
                bill, created = Bill.objects.update_or_create(
                    number=bill_number,
                    defaults={
                        'title': bill_title,
                        'last_updated': timezone.now(),
                    }
                )

                action = "creado" if created else "actualizado"
                self.stdout.write(f"  💾 Bill {action}: {bill.number}")

                # Fase 7: Análisis de IA (Gemini)
                try:
                    # Avoid duplicate AI calls: if already has a positive ai_score, skip.
                    try:
                        existing_score = int(getattr(bill, 'ai_score', 0) or 0)
                    except Exception:
                        existing_score = 0

                    ai_called = False
                    if existing_score > 0:
                        self.stdout.write("  ⏩ Saltando IA (ya analizado)")
                    else:
                        self.stdout.write("  🤖 Analizando con IA...")
                        result = analyze_bill_relevance(bill)
                        ai_called = True
                        if result and isinstance(result, dict):
                            score = int(result.get('score', 0))
                            analysis = result.get('analysis', '')
                            bill.ai_score = score
                            bill.ai_analysis = analysis
                            bill.relevance_why = (analysis[:500] if analysis else '')
                            bill.save(update_fields=['ai_score', 'ai_analysis', 'relevance_why'])
                            self.stdout.write(f"  🤖 AI score: {score}")
                except Exception as e:
                    logger.error("AI analysis failed for %s: %s", bill.number, e, exc_info=True)

                success_count += 1

            except Exception as e:
                self.stdout.write(f"  ❌ Error procesando {measure_id}: {str(e)}")
                logger.error(f"Robot error en {measure_id}: {e}", exc_info=True)
                error_count += 1

            # Rate limiting to avoid overwhelming SUTRA server
            try:
                if 'ai_called' in locals() and ai_called:
                    self.stdout.write("  ⏳ Pausa de seguridad (10s) para cuidar la cuota...")
                    time.sleep(10)
                else:
                    time.sleep(1)
            except Exception:
                # Fallback single-second wait on any unexpected issue
                time.sleep(1)
            self.stdout.write("-" * 80)

        # Final summary
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS(f"✅ Escaneo completado"))
        self.stdout.write(f"  • Exitosos: {success_count}")
        self.stdout.write(f"  • Saltados: {skip_count}")
        self.stdout.write(f"  • Errores: {error_count}")
        self.stdout.write(f"  • Total procesados: {len(measures_to_process)}")
        self.stdout.write("=" * 80)