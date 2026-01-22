import feedparser
import requests
from bs4 import BeautifulSoup
from dateutil import parser
from .models import NewsSource, Article, NewsPreset
from django.utils import timezone
import google.generativeai as genai
import unicodedata
import time
import datetime
import difflib
import urllib3

# Desactivar las advertencias molestas de seguridad SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- TU CLAVE DE GOOGLE ---
GOOGLE_API_KEY = "AIzaSyBl561zpgqQlziXDPvy6yvrBHJ_-GQ7_-M"

genai.configure(api_key=GOOGLE_API_KEY)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9',
    'Referer': 'https://www.google.com/'
}

# --- 1. COMPARADOR VISUAL (COLORES) ---
def generate_diff_html(text1, text2):
    lines1 = text1.splitlines()
    lines2 = text2.splitlines()
    d = difflib.HtmlDiff()
    html_diff = d.make_table(lines1, lines2, fromdesc='Versión A', todesc='Versión B', context=True, numlines=5)
    html_diff = html_diff.replace('nowrap="nowrap"', '')
    return html_diff

# --- 2. COMPARADOR INTELIGENTE (IA) ---
def analyze_legal_diff(text_old, text_new):
    try:
        available_model = None
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_model = m.name
                    break 
        except: pass
        
        if not available_model: available_model = 'models/gemini-1.5-flash'
        
        model = genai.GenerativeModel(available_model)
        
        prompt = f"""
        Actúa como un Abogado Corporativo Senior. Compara los textos y genera un Resumen Ejecutivo.
        
        REGLAS DE FORMATO ESTRICTAS (NO LAS ROMPAS):
        1. NO saludes, NO des introducciones.
        2. Tu respuesta debe ser EXCLUSIVAMENTE código HTML.
        3. Usa la etiqueta <h3> para el título principal.
        4. Usa la etiqueta <ul class="list-disc pl-5 space-y-2"> para la lista de puntos.
        5. Cada punto debe ser un <li> con <strong>Concepto:</strong>.

        --- VERSIÓN ORIGINAL ---
        {text_old}

        --- VERSIÓN NUEVA ---
        {text_new}
        """
        
        response = model.generate_content(prompt)
        clean_text = response.text.replace("```html", "").replace("```", "")
        return clean_text

    except Exception as e:
        return f"<p class='text-red-500'><strong>Error analizando con IA:</strong> {str(e)}</p>"

# --- 3. FUNCIONES DEL ROBOT DE NOTICIAS ---
def normalize_text(text):
    if not text: return ""
    text = text.lower()
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

def scrape_full_text(url):
    try:
        time.sleep(0.3) 
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.encoding = 'utf-8'
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.text, 'html.parser')
        full_text = ""
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            text = p.get_text().strip()
            if len(text) > 40 and "Copyright" not in text and "Suscríbete" not in text:
                full_text += f"<p>{text}</p>"
        return full_text if len(full_text) > 100 else None
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def get_image_from_entry(entry):
    if 'media_content' in entry:
        for media in entry.media_content:
            if 'image' in media.get('type', '') or 'jpg' in media.get('url', ''): return media['url']
    if 'enclosures' in entry:
        for enclosure in entry.enclosures:
            if 'image' in enclosure.get('type', ''): return enclosure['href']
    if 'media_thumbnail' in entry: return entry.media_thumbnail[0]['url']
    return None

# --- FUNCIONES DE SINCRONIZACIÓN RSS ---

def get_active_sources():
    """Obtiene todas las fuentes RSS activas."""
    return NewsSource.objects.filter(is_active=True)

def get_active_presets():
    """Obtiene todos los presets de filtrado activos."""
    return NewsPreset.objects.filter(is_active=True)

def check_match(text, presets):
    """
    Verifica si un texto coincide con los keywords de algún preset.
    Retorna: (match: bool, preset_name: str)
    """
    if not presets: 
        return True, None
    
    text_normalized = normalize_text(text)
    
    for preset in presets:
        keywords = [k.strip() for k in preset.keywords.split(',')]
        for keyword in keywords:
            if not keyword: 
                continue
            if normalize_text(keyword) in text_normalized:
                return True, preset.name
    
    return False, None

def article_exists(link):
    """Verifica si un artículo ya existe en la base de datos por URL."""
    return Article.objects.filter(link=link).exists()

def extract_article_date(entry):
    """Extrae la fecha de publicación de una entrada RSS."""
    if hasattr(entry, 'published'):
        try:
            return parser.parse(entry.published)
        except:
            pass
    return timezone.now()

def create_article_from_entry(source, entry, snippet, image_url, preset_name=None):
    """
    Crea un artículo en la base de datos desde una entrada RSS.
    Retorna el artículo creado.
    """
    article = Article.objects.create(
        source=source,
        title=entry.title,
        link=entry.link,
        published_at=extract_article_date(entry),
        snippet=snippet,
        image_url=image_url
    )
    
    print(f"✅ NUEVA: '{entry.title[:50]}...' (Preset: {preset_name or 'N/A'})")
    return article

def process_rss_entry(source, entry, active_presets):
    """
    Procesa una entrada RSS individual con filtrado en dos pasadas.
    
    Primera pasada: Filtra por título y snippet del feed (rápido)
    Segunda pasada: Descarga contenido y confirma relevancia (exhaustivo)
    
    Retorna: True si se creó un artículo, False si no.
    """
    link = entry.link
    
    # Evitar duplicados
    if article_exists(link):
        return False
    
    title = entry.title
    feed_snippet = entry.summary if hasattr(entry, 'summary') else ""
    
    # PRIMERA PASADA: Filtro rápido en título + snippet del feed
    # Esto ahorra descargas innecesarias
    preliminary_text = title + " " + feed_snippet
    match_preliminary, preset_name = check_match(preliminary_text, active_presets)
    
    if not match_preliminary:
        # No pasa filtro preliminar, descartamos sin descargar
        return False
    
    print(f"📌 Filtro preliminar OK: '{title[:50]}...' (Preset: {preset_name})")
    
    # SEGUNDA PASADA: Descargar contenido completo y confirmar
    full_content = scrape_full_text(link)
    if not full_content:
        # Si no se pudo scraping completo, usar snippet del feed
        full_content = feed_snippet if feed_snippet else title
    
    # Confirmar relevancia con contenido completo
    match_final, final_preset = check_match(title + " " + full_content, active_presets)
    
    if not match_final:
        # Pasó preliminar pero no confirmación (falso positivo)
        print(f"  ⚠️  Descartado tras análisis completo (falso positivo)")
        return False
    
    # Obtener imagen
    image_url = get_image_from_entry(entry)
    
    # Crear artículo confirmado como relevante
    create_article_from_entry(source, entry, full_content, image_url, final_preset)
    
    return True

def sync_rss_source(source, active_presets, max_entries=10):
    """
    Sincroniza una fuente RSS individual.
    Retorna: cantidad de artículos nuevos creados.
    """
    try:
        feed = feedparser.parse(source.url, request_headers=HEADERS)
        new_count = 0
        
        for entry in feed.entries[:max_entries]:
            if process_rss_entry(source, entry, active_presets):
                new_count += 1
        
        return new_count
        
    except Exception as e:
        print(f"❌ Error en fuente {source.name}: {e}")
        return 0

def clean_invalid_articles():
    """
    Elimina artículos que ya no coinciden con los presets activos.
    Retorna: cantidad de artículos eliminados.
    """
    print("--- RE-VALIDANDO ARTÍCULOS EXISTENTES ---")
    
    active_presets = get_active_presets()
    articles = Article.objects.all()
    deleted_count = 0
    
    for article in articles:
        full_content = article.snippet or ""
        match, _ = check_match(article.title + " " + full_content, active_presets)
        
        if not match:
            article.delete()
            deleted_count += 1
    
    print(f"--- LIMPIEZA: {deleted_count} artículos eliminados ---\n")
    return deleted_count

def sync_all_rss_sources(max_entries=10, clean_first=True):
    """
    Sincroniza todas las fuentes RSS activas.
    
    Args:
        max_entries: Número máximo de entradas a procesar por fuente
        clean_first: Si True, limpia artículos inválidos antes de sincronizar
    
    Retorna: cantidad total de artículos nuevos.
    """
    # Limpiar artículos obsoletos
    if clean_first:
        clean_invalid_articles()
    
    # Obtener fuentes y presets activos
    sources = get_active_sources()
    active_presets = get_active_presets()
    
    if not sources.exists():
        print("⚠️ No hay fuentes RSS activas")
        return 0
    
    print(f"--- SINCRONIZANDO {sources.count()} FUENTES RSS ---")
    
    total_new = 0
    for source in sources:
        new_count = sync_rss_source(source, active_presets, max_entries)
        total_new += new_count
    
    print(f"\n--- TOTAL: {total_new} artículos nuevos ---")
    return total_new

# Alias para compatibilidad con código existente
def fetch_latest_news():
    """Función legacy - mantiene compatibilidad con código existente."""
    return sync_all_rss_sources(max_entries=10, clean_first=True)

def sync_database_with_filters():
    """Función legacy - mantiene compatibilidad con código existente."""
    return clean_invalid_articles()

def calculate_content_hash(text):
    """Calcula un hash MD5 del contenido para validación de caché."""
    import hashlib
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def chunk_text(text, max_words=800):
    """
    Divide un texto largo en fragmentos manejables.
    
    Args:
        text: Texto a dividir
        max_words: Máximo de palabras por fragmento
    
    Retorna: Lista de fragmentos de texto
    """
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), max_words):
        chunk = ' '.join(words[i:i + max_words])
        chunks.append(chunk)
    
    return chunks

def get_available_gemini_model():
    """Obtiene un modelo Gemini disponible."""
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                return m.name
    except:
        pass
    return 'models/gemini-1.5-flash'

def summarize_text_chunk(model, chunk, is_final=False):
    """
    Resume un fragmento de texto individual.
    
    Args:
        model: Modelo Gemini configurado
        chunk: Texto del fragmento
        is_final: Si es el resumen final (combina chunks previos)
    
    Retorna: Texto del resumen
    """
    if is_final:
        # Resumen final que combina mini-resúmenes
        prompt = """
Resume el siguiente contenido en 3-5 puntos clave siguiendo el formato de las 5W del periodismo.
Usa HTML con viñetas (<ul><li>). Estructura:

1. QUÉ/QUIÉN: El hecho principal y protagonistas
2. DÓNDE/CUÁNDO: Ubicación y tiempo del evento
3. POR QUÉ/CÓMO: Contexto, causas o método
4. IMPACTO: Consecuencias o importancia
5. QUÉ SIGUE (si aplica): Próximos pasos o situación futura

Sé conciso, objetivo y claro. Usa español neutral.

Texto a resumir:
""" + chunk
    else:
        # Resumen de un fragmento individual
        prompt = f"""
Resume los puntos principales del siguiente fragmento de noticia de forma concisa.
Enfócate en hechos concretos, protagonistas y datos relevantes.

Fragmento:
{chunk}
"""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error resumiendo fragmento: {str(e)}"

def generate_ai_summary(article_id):
    """
    Genera un resumen IA para un artículo usando chunking para textos largos.
    Implementa formato 5W (quién, qué, dónde, cuándo, por qué).
    Valida caché de resúmenes usando content_hash.
    """
    try:
        article = Article.objects.get(id=article_id)
        
        # Obtener contenido a resumir
        content = article.snippet or ""
        if not content or len(content) < 100:
            article.ai_summary = "⚠️ <strong>Contenido insuficiente</strong> para generar resumen."
            article.save()
            return False
        
        # Calcular hash del contenido actual
        current_hash = calculate_content_hash(content)
        
        # Verificar si ya existe un resumen válido
        if article.ai_summary and article.content_hash == current_hash:
            print(f"📋 Resumen en caché válido para: {article.title[:50]}...")
            return True  # Resumen existente y válido, no regenerar
        
        # Si el hash no coincide o no hay resumen, generamos uno nuevo
        if article.ai_summary and article.content_hash != current_hash:
            print(f"🔄 Contenido modificado, regenerando resumen...")
        
        # Obtener modelo disponible
        model_name = get_available_gemini_model()
        model = genai.GenerativeModel(model_name)
        
        # Determinar si necesitamos chunking
        word_count = len(content.split())
        
        if word_count <= 800:
            # Texto corto - resumen directo
            summary = summarize_text_chunk(model, content, is_final=True)
        else:
            # Texto largo - dividir en chunks, resumir cada uno, luego combinar
            print(f"📄 Artículo largo ({word_count} palabras) - usando chunking")
            
            chunks = chunk_text(content, max_words=800)
            chunk_summaries = []
            
            for i, chunk in enumerate(chunks):
                print(f"  Resumiendo fragmento {i+1}/{len(chunks)}...")
                chunk_summary = summarize_text_chunk(model, chunk, is_final=False)
                chunk_summaries.append(chunk_summary)
                time.sleep(0.5)  # Pequeña pausa entre chunks
            
            # Combinar resúmenes de chunks y hacer resumen final
            combined = "\n\n".join(chunk_summaries)
            print(f"  Generando resumen final...")
            summary = summarize_text_chunk(model, combined, is_final=True)
        
        # Guardar resumen y hash
        article.ai_summary = summary
        article.content_hash = current_hash
        article.save()
        
        print(f"✅ Resumen generado para: {article.title[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ Error generando resumen: {str(e)}")
        article.ai_summary = f"⚠️ <strong>ERROR TÉCNICO:</strong> {str(e)}"
        article.save()
        return False

# --- 4. ROBOT DE SUTRA (MODO INSEGURO ACTIVADO) ---
def check_sutra_status(measure_id):
    """
    Verifica estado en SUTRA ignorando errores SSL.
    """
    clean_id = measure_id.lower().replace("p. de la c.", "pc").replace(" ", "").replace(".", "")
    base_url = f"https://sutra.oslpr.org/osl/es/medidas/{clean_id}"
    
    try:
        # verify=False ES LA CLAVE PARA ARREGLAR TU ERROR
        response = requests.get(base_url, headers=HEADERS, timeout=10, verify=False)
        
        if response.status_code == 200:
            return True, f"Conexión exitosa: {base_url}"
        else:
            return False, f"No encontrado (Status {response.status_code})"
    except Exception as e:
        return False, f"Error de conexión: {str(e)}"