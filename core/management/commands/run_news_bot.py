from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Article
from core.utils import fetch_latest_news
import datetime

class Command(BaseCommand):
    help = 'Borra noticias viejas y descarga nuevas automáticamnte'

    def handle(self, *args, **options):
        self.stdout.write("--- INICIANDO ROBOT DE NOTICIAS ---")

        # 1. BORRADO DE LIMPIEZA (7 DÍAS)
        # Calculamos la fecha de hace 7 días
        limite = timezone.now() - datetime.timedelta(days=7)
        # Borramos todo lo que sea anterior a esa fecha
        deleted_count, _ = Article.objects.filter(published_at__lt=limite).delete()
        self.stdout.write(f"1. LIMPIEZA: Se borraron {deleted_count} noticias de hace más de una semana.")

        # 2. DESCARGA DE NUEVAS (Usando tus filtros y scraping)
        self.stdout.write("2. ACTUALIZACIÓN: Buscando noticias nuevas...")
        try:
            new_articles = fetch_latest_news()
            self.stdout.write(f"   -> Se guardaron {new_articles} noticias nuevas.")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   -> Error al actualizar: {e}"))

        self.stdout.write("--- FIN DEL PROCESO ---")