import time

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import SystemSettings


class Command(BaseCommand):
    help = "Servicio Inteligente: Alterna entre modo Intensivo y Pasivo según configuración"

    def handle(self, *args, **options):
        self.stdout.write("--- 🧠 INICIANDO CEREBRO AUTOMATIZADO ---")
        self.stdout.write("--- Basado en configuración del Panel de Control ---")

        while True:
            try:
                # Obtener la configuración (o crear una por defecto si no existe)
                config = SystemSettings.objects.first()
                if not config:
                    config = SystemSettings.objects.create()

                # 1. Verificar si está apagado globalmente
                if not config.is_active:
                    self.stdout.write(
                        "💤 Sistema pausado desde Admin. Esperando 1 min..."
                    )
                    time.sleep(60)
                    continue

                # 2. Calcular fecha y hora actual (Puerto Rico)
                now = timezone.localtime(timezone.now())
                current_time = now.time()
                current_weekday = str(now.weekday())  # 0=Lunes, 6=Domingo

                # 3. Lógica de Decisión
                # ¿Es día laborable configurado?
                dias_laborables = config.active_days.split(",")
                es_dia_trabajo = current_weekday in dias_laborables

                # ¿Estamos en horario intensivo?
                es_horario_trabajo = (
                    config.high_freq_start <= current_time <= config.high_freq_end
                )

                # Determinar intervalo
                if es_dia_trabajo and es_horario_trabajo:
                    modo = "🔥 INTENSIVO"
                    intervalo = config.high_freq_interval
                else:
                    modo = "🌙 PASIVO"
                    intervalo = config.low_freq_interval

                # 4. Ejecutar Robot
                self.stdout.write(
                    f"[{now.strftime('%H:%M')}] Modo: {modo} | Próximo: {intervalo} min."
                )

                call_command("ejecutar_robot")

                # 5. Dormir según el intervalo decidido
                time.sleep(intervalo * 60)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error crítico en loop: {e}"))
                time.sleep(30)
