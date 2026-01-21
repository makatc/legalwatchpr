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

def check_match(text, presets):
    if not presets: return True 
    text_normalized = normalize_text(text)
    for preset in presets:
        keywords = [k.strip() for k in preset.keywords.split(',')]
        for k in keywords:
            if not k: continue
            if normalize_text(k) in text_normalized:
                return True, preset.name 
    return False, None

def sync_database_with_filters():
    print("--- RE-VALIDANDO NOTICIAS EXISTENTES ---")
    active_presets = NewsPreset.objects.filter(is_active=True)
    articles = Article.objects.all()
    deleted_count = 0
    for article in articles:
        full_content = article.snippet
        match, _ = check_match(article.title + " " + full_content, active_presets)
        if not match:
            article.delete()
            deleted_count += 1
    print(f"--- LIMPIEZA COMPLETADA: {deleted_count} noticias eliminadas ---\n")

def fetch_latest_news():
    sync_database_with_filters()
    sources = NewsSource.objects.filter(is_active=True)
    active_presets = NewsPreset.objects.filter(is_active=True)
    total_new = 0
    print(f"--- BUSCANDO NUEVAS NOTICIAS ---")
    for source in sources:
        try:
            feed = feedparser.parse(source.url, request_headers=HEADERS)
            for entry in feed.entries[:10]:
                link = entry.link
                if Article.objects.filter(link=link).exists(): continue
                title = entry.title
                full_content = scrape_full_text(link)
                if not full_content: full_content = entry.summary if hasattr(entry, 'summary') else title
                match, preset_name = check_match(title + " " + full_content, active_presets)
                if match: 
                    print(f"✅ NUEVA ENCONTRADA: '{title[:30]}...' (Tema: {preset_name})")
                    pub_date = timezone.now()
                    if hasattr(entry, 'published'):
                        try: pub_date = parser.parse(entry.published)
                        except: pass
                    img = get_image_from_entry(entry)
                    Article.objects.create(
                        source=source, title=title, link=link, 
                        published_at=pub_date, snippet=full_content, image_url=img
                    )
                    total_new += 1
        except Exception as e: print(f"Error {source.name}: {e}")
    return total_new

def generate_ai_summary(article_id):
    try:
        article = Article.objects.get(id=article_id)
        available_model = None
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_model = m.name
                    break 
        except: pass
        if not available_model: available_model = 'models/gemini-1.5-flash'
        
        model = genai.GenerativeModel(available_model)
        prompt = (
            "Eres un analista experto. Resume el siguiente texto en 3 puntos clave (HTML <ul><li>). "
            f"\n\nNoticia: {article.title}\n{article.snippet}"
        )
        response = model.generate_content(prompt)
        article.ai_summary = response.text
        article.save()
        return True
    except Exception as e:
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