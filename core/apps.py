from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = "1. CONFIGURACIÓN DE BÚSQUEDA" # Esto lo pone arriba de todo
    
    def ready(self):
        """Se ejecuta cuando Django arranca. Inicia el scheduler automático."""
        import sys
        import threading
        
        # Registrar tipo vector de pgvector
        try:
            from django.db import connection
            from pgvector.psycopg2 import register_vector
            try:
                with connection.cursor() as cursor:
                    register_vector(cursor.connection)
            except Exception as e:
                # Ignorar si pgvector no está instalado o ya registrado
                pass
        except ImportError:
            pass
        
        if 'runserver' in sys.argv or 'gunicorn' in sys.argv[0]:
            # Ejecutar scheduler con delay para evitar warning de DB
            def delayed_start():
                import time
                time.sleep(2)  # Esperar a que Django esté listo
                from .scheduler import start_scheduler
                start_scheduler()
            
            thread = threading.Thread(target=delayed_start, daemon=True)
            thread.start()
