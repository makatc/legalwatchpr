from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = "1. CONFIGURACIÓN DE BÚSQUEDA" # Esto lo pone arriba de todo
    
    def ready(self):
        """Se ejecuta cuando Django arranca. Inicia el scheduler automático."""
        import sys
        if 'runserver' in sys.argv or 'gunicorn' in sys.argv[0]:
            from .scheduler import start_scheduler
            start_scheduler()
