import feedparser
import logging
from django.utils import timezone
from email.utils import parsedate_to_datetime
from core.models import Article, NewsSource

logger = logging.getLogger(__name__)

def parse_date(date_str):
    """
    Parsea fechas de RSS y asegura que sean 'Timezone Aware' para evitar warnings de Django.
    """
    if not date_str:
        return timezone.now()
    try:
        # Intento estándar RFC 822
        dt = parsedate_to_datetime(date_str)
        if dt:
            # FIX CRÍTICO: Convertir a aware si es naive
            if timezone.is_naive(dt):
                return timezone.make_aware(dt)
            return dt
    except Exception:
        # Si falla el parseo, usar fecha actual
        pass
    return timezone.now()

def sync_all_rss_sources(max_entries=10, clean_first=False):
    """
    Descarga noticias de todas las fuentes activas.
    Retorna el número de artículos nuevos creados.
    """
    sources = NewsSource.objects.filter(is_active=True)
    total_created = 0
    
    print(f"\n--- 📡 SINCRONIZACIÓN RSS ({len(sources)} fuentes) ---")

    for source in sources:
        try:
            feed = feedparser.parse(source.url)
            # Ignoramos bozo_exception si logramos sacar entradas
            entries = feed.entries[:max_entries]
            created_count = 0
            
            for entry in entries:
                link = entry.get('link', '')
                if not link: continue

                # Deduplicación por URL
                if Article.objects.filter(link=link).exists():
                    continue
                
                title = entry.get('title', '')[:500]
                snippet = entry.get('summary', '') or entry.get('description', '')
                published_at = parse_date(entry.get('published', entry.get('updated')))
                
                Article.objects.create(
                    title=title,
                    link=link,
                    snippet=snippet,
                    published_at=published_at,
                    source=source,
                    search_vector=None # Se llenará con el trigger de DB
                )
                created_count += 1
            
            if created_count > 0:
                print(f"   ✅ {source.name}: +{created_count} noticias")
            total_created += created_count

        except Exception as e:
            print(f"   ❌ Error en {source.name}: {str(e)}")
            logger.error(f"Error syncing {source.name}: {e}")

    print(f"--- FIN: {total_created} noticias nuevas ---\n")
    return total_created