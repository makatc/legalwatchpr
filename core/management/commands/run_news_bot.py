import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Article
from core.utils import sync_all_rss_sources


class Command(BaseCommand):
    help = "Sincroniza noticias RSS desde fuentes activas con filtros por presets"

    def add_arguments(self, parser):
        parser.add_argument(
            "--max-entries",
            type=int,
            default=10,
            help="Número máximo de entradas a procesar por fuente (default: 10)",
        )
        parser.add_argument(
            "--no-clean",
            action="store_true",
            help="No limpiar artículos inválidos antes de sincronizar",
        )
        parser.add_argument(
            "--delete-old",
            type=int,
            help="Eliminar artículos con más de N días (ej: 7)",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=== ROBOT DE NOTICIAS RSS ===\n"))

        # 1. ELIMINAR ARTÍCULOS ANTIGUOS (OPCIONAL)
        if options["delete_old"]:
            days = options["delete_old"]
            limite = timezone.now() - datetime.timedelta(days=days)
            deleted_count, _ = Article.objects.filter(published_at__lt=limite).delete()
            self.stdout.write(
                f"🗑️  Eliminados {deleted_count} artículos de hace más de {days} días\n"
            )

        # 2. SINCRONIZAR NOTICIAS RSS
        self.stdout.write("📡 Iniciando sincronización RSS...")

        try:
            clean_first = not options["no_clean"]
            max_entries = options["max_entries"]

            new_articles = sync_all_rss_sources(
                max_entries=max_entries, clean_first=clean_first
            )

            if new_articles > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n✅ Se agregaron {new_articles} artículos nuevos"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING("\n⚠️  No se encontraron artículos nuevos")
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"\n❌ Error durante sincronización: {e}")
            )
            raise

        self.stdout.write(self.style.SUCCESS("\n=== PROCESO COMPLETADO ==="))
