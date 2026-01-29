"""
Django Management Command: Sync Bills from SUTRA
=================================================

Sincroniza medidas legislativas desde el Sistema SUTRA de Puerto Rico.

Uso:
    python manage.py sync_bills
    python manage.py sync_bills --limit 50
    python manage.py sync_bills --chamber S --start 500
    python manage.py sync_bills --ids "P. de la C. 1001" "P. del S. 250"
"""

from django.core.management.base import BaseCommand, CommandError

from core.utils.sutra_sync import sync_sutra_bills, sync_specific_bills


class Command(BaseCommand):
    help = 'Sincroniza medidas legislativas desde SUTRA'

    def add_arguments(self, parser):
        """Define argumentos del comando."""
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Número de medidas a intentar sincronizar (default: 10)'
        )
        
        parser.add_argument(
            '--chamber',
            type=str,
            choices=['C', 'S'],
            default='C',
            help='Cámara: C (Cámara de Representantes) o S (Senado) (default: C)'
        )
        
        parser.add_argument(
            '--start',
            type=int,
            default=1000,
            help='Número inicial de medida (default: 1000)'
        )
        
        parser.add_argument(
            '--ids',
            nargs='+',
            help='Lista de IDs específicos a sincronizar (ej: "P. de la C. 1001" "P. del S. 250")'
        )

    def handle(self, *args, **options):
        """Ejecuta la sincronización."""
        limit = options['limit']
        chamber = options['chamber']
        start_number = options['start']
        specific_ids = options.get('ids')
        
        try:
            self.stdout.write(
                self.style.WARNING('\n🔄 Iniciando sincronización SUTRA...\n')
            )
            
            if specific_ids:
                # Sincronización específica
                self.stdout.write(f"Modo: Sincronización específica de {len(specific_ids)} medidas")
                synced_count = sync_specific_bills(specific_ids)
            else:
                # Sincronización por rango
                chamber_name = 'Cámara de Representantes' if chamber == 'C' else 'Senado'
                self.stdout.write(f"Modo: Sincronización por rango")
                self.stdout.write(f"Cámara: {chamber_name}")
                self.stdout.write(f"Rango: {start_number} - {start_number + limit - 1}")
                
                synced_count = sync_sutra_bills(
                    limit=limit,
                    chamber=chamber,
                    start_number=start_number
                )
            
            # Mostrar resultado
            if synced_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'\n✅ Sincronización completada: {synced_count} medidas')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('\n⚠️ No se sincronizó ninguna medida')
                )
        
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('\n\n⏸️ Sincronización interrumpida por el usuario')
            )
            raise CommandError('Operación cancelada')
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n❌ Error durante la sincronización: {e}')
            )
            raise CommandError(f'Falló la sincronización: {e}')
