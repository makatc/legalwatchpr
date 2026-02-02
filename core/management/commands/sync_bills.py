"""
Django Management Command: Sync Bills from SUTRA
=================================================

Sincroniza medidas legislativas desde el Sistema SUTRA de Puerto Rico.
Usa la lógica unificada de core.utils.legislative.
"""

from django.core.management.base import BaseCommand, CommandError

from core.utils.legislative import sync_bills_range, sync_specific_bills


class Command(BaseCommand):
    help = "Sincroniza medidas legislativas desde SUTRA"

    def add_arguments(self, parser):
        """Define argumentos del comando."""
        parser.add_argument(
            "--limit",
            type=int,
            default=10,
            help="Número de medidas a intentar sincronizar (default: 10)",
        )

        parser.add_argument(
            "--chamber",
            type=str,
            choices=["C", "S"],
            default="C",
            help="Cámara: C (Cámara de Representantes) o S (Senado) (default: C)",
        )

        parser.add_argument(
            "--start",
            type=int,
            default=1000,
            help="Número inicial de medida (default: 1000)",
        )

        parser.add_argument(
            "--ids",
            nargs="+",
            help='Lista de IDs específicos a sincronizar (ej: "P. de la C. 1001" "P. del S. 250")',
        )

        parser.add_argument(
            "--skip-ai",
            action="store_true",
            help="Saltar el análisis de IA durante la sincronización",
        )

    def handle(self, *args, **options):
        """Ejecuta la sincronización."""
        limit = options["limit"]
        chamber = options["chamber"]
        start_number = options["start"]
        specific_ids = options.get("ids")
        run_ai = not options["skip_ai"]

        try:
            self.stdout.write(
                self.style.WARNING("\n🔄 Iniciando sincronización SUTRA...\n")
            )

            if specific_ids:
                self.stdout.write(
                    f"Modo: Sincronización específica de {len(specific_ids)} medidas"
                )
                synced_count = sync_specific_bills(specific_ids, run_ai=run_ai)
            else:
                chamber_name = "Cámara de Representantes" if chamber == "C" else "Senado"
                self.stdout.write(f"Modo: Sincronización por rango ({chamber_name})")
                self.stdout.write(f"Rango: {start_number} - {start_number + limit - 1}")

                synced_count = sync_bills_range(
                    chamber=chamber,
                    start=start_number,
                    limit=limit,
                    run_ai=run_ai
                )

            if synced_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\n✅ Sincronización completada: {synced_count} medidas"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING("\n⚠️ No se sincronizó ninguna medida")
                )

        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING("\n\n⏸️ Sincronización interrumpida por el usuario")
            )
            raise CommandError("Operación cancelada")

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"\n❌ Error durante la sincronización: {e}")
            )
            raise CommandError(f"Falló la sincronización: {e}")
