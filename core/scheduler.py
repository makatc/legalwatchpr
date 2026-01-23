"""
Configuración del Scheduler Automático para Sincronización de Noticias.
Usa APScheduler para ejecutar tareas periódicas.
"""

import logging
import sys

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

# Instancia global del scheduler
scheduler = None

def sync_news_task():
    """
    Tarea que sincroniza noticias RSS automáticamente.
    Se ejecuta cada 30 minutos.
    """
    from core.utils import sync_all_rss_sources
    
    logger.info("🤖 Iniciando sincronización automática de noticias...")
    try:
        new_count = sync_all_rss_sources(max_entries=15, clean_first=True)
        logger.info(f"✅ Sincronización completada: {new_count} artículos nuevos")
    except Exception as e:
        logger.error(f"❌ Error en sincronización automática: {e}")

def start_scheduler():
    """
    Inicia el scheduler de tareas automáticas.
    Se llama desde apps.py cuando Django arranca.
    """
    global scheduler
    
    # Solo ejecutar en runserver o gunicorn
    if not ('runserver' in sys.argv or 'gunicorn' in sys.argv[0]):
        return
    
    # Evitar inicializar dos veces
    if scheduler is not None and scheduler.running:
        return
    
    # Usar scheduler en memoria (sin DjangoJobStore para evitar warning)
    scheduler = BackgroundScheduler()
    
    # Tarea: Sincronizar noticias cada 30 minutos
    scheduler.add_job(
        sync_news_task,
        trigger=IntervalTrigger(minutes=30),
        id="sync_news_every_30min",
        name="Sincronizar Noticias RSS",
        replace_existing=True,
        max_instances=1,  # Solo una instancia a la vez
    )
    
    try:
        print("⏰ Scheduler iniciado - Sincronización automática cada 30 minutos")
        logger.info("⏰ Scheduler iniciado - Sincronización automática cada 30 minutos")
        scheduler.start()
    except Exception as e:
        logger.error(f"Error iniciando scheduler: {e}")
