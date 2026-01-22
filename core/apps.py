from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = "1. CONFIGURACIÓN DE BÚSQUEDA" # Esto lo pone arriba de todo
    
    def ready(self):
        """Se ejecuta cuando Django arranca. Inicia el scheduler automático."""
        import sys
        import threading
        
        if 'runserver' in sys.argv or 'gunicorn' in sys.argv[0]:
            # Ejecutar scheduler con delay para evitar warning de DB
            def delayed_start():
                import time
                time.sleep(2)  # Esperar a que Django esté listo
                from .scheduler import start_scheduler
                start_scheduler()
            
            thread = threading.Thread(target=delayed_start, daemon=True)
            thread.start()
