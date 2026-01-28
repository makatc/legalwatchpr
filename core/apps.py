from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = "1. CONFIGURACIÓN DE BÚSQUEDA" # Esto lo pone arriba de todo
    
    def ready(self):
        """Se ejecuta cuando Django arranca.

        Mantener este método liviano: registrar señales/receivers y evitar
        arrancar schedulers, hilos o inicializaciones pesadas aquí.
        Use comandos de management o procesos separados para iniciar
        servicios largos (p. ej. schedulers, workers, registros DB especiales).
        """
        # Evitar doble inicialización en entornos que llaman ready() varias veces
        if getattr(self, "_ready_done", False):
            return

        # Registrar señales ligeras (si existen). No debe lanzar excepción si falta.
        try:
            from . import signals  # noqa: F401
        except Exception:
            # No fallamos el arranque por errores en el módulo de señales
            pass

        # NOTA: no iniciar pgvector index creation ni schedulers aquí.
        # Es más seguro exponer management commands para esas tareas.

        self._ready_done = True
