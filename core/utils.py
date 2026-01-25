import os
import difflib
import unicodedata
try:
    import google.generativeai as genai
except Exception:
    genai = None
import requests
import urllib3
from dotenv import load_dotenv

# --- 1. CONFIGURACIÓN DE RUTAS ---
BASE_DIR = r"C:\Users\becof\vs\legalwatchpr"
# load .env from absolute path as requested
ENV_PATH = r"C:\Users\becof\vs\legalwatchpr\.env"

if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)
    print(f"✅ Archivo .env cargado desde: {ENV_PATH}")
else:
    # attempt to load anyway; load_dotenv is safe if file missing
    load_dotenv(ENV_PATH)
    print(f"❌ ERROR: No se encontró el .env en: {ENV_PATH}")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY and genai is not None:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
    except Exception:
        pass

# --- 2. FUNCIONES REQUERIDAS POR VIEWS.PY ---

def analyze_legal_diff(text_old, text_new):
    """Analiza cambios entre dos textos y devuelve un resumen estructurado.

    Usa la IA si está disponible; si no, hace un análisis local con difflib.
    """
    try:
        if genai is not None and GOOGLE_API_KEY:
            try:
                model = getattr(genai, 'GenerativeModel', None)
                if model:
                    m = model('gemini-1.5-flash')
                    response = m.generate_content(f"Compara y resume estos textos legales: {text_old[:2000]} vs {text_new[:2000]}")
                    return getattr(response, 'text', str(response))
            except Exception:
                # fallthrough to local analysis
                pass

        a = text_old or ""
        b = text_new or ""
        na = normalize_text(a)
        nb = normalize_text(b)
        sm = difflib.SequenceMatcher(a=na, b=nb)
        opcodes = sm.get_opcodes()

        added = []
        removed = []
        changed = []
        for tag, i1, i2, j1, j2 in opcodes:
            a_seg = na[i1:i2]
            b_seg = nb[j1:j2]
            if tag == 'insert':
                added.append({'text': b_seg, 'pos': j1})
            elif tag == 'delete':
                removed.append({'text': a_seg, 'pos': i1})
            elif tag == 'replace':
                changed.append({'from': a_seg, 'to': b_seg, 'pos_from': i1, 'pos_to': j1})

        html = generate_diff_html(a, b)
        return {
            'added': added,
            'removed': removed,
            'changed': changed,
            'html': html,
            'summary': {
                'added_count': len(added),
                'removed_count': len(removed),
                'changed_count': len(changed),
            },
        }
    except Exception as e:
        return {'error': str(e)}

def check_sutra_status(measure_id):
    """Verifica conexión con SUTRA ignorando SSL"""
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    clean_id = str(measure_id).lower().replace("p. de la c.", "pc").replace(" ", "").replace(".", "")
    url = f"https://sutra.oslpr.org/osl/es/medidas/{clean_id}"
    try:
        res = requests.get(url, timeout=10, verify=False, headers={'User-Agent': 'Mozilla/5.0'})
        return (res.status_code == 200, "En línea" if res.status_code == 200 else f"Error {res.status_code}")
    except Exception as e:
        return (False, str(e))

def generate_diff_html(text1, text2):
    """Genera tabla de diferencias visuales"""
    d = difflib.HtmlDiff()
    return d.make_table(text1.splitlines() if text1 else [], text2.splitlines() if text2 else [], context=True)

def fetch_latest_news(limit=10):
    """Fetch latest news/articles by syncing RSS sources."""
    from core.scraper import sync_all_rss_sources
    return sync_all_rss_sources(max_entries=10)

def generate_ai_summary(article_id):
    """Generate an AI summary for an article using Gemini API."""
    from core.models import Article
    try:
        article = Article.objects.get(id=article_id)
        if not os.getenv("GOOGLE_API_KEY"):
            return "Error: API Key missing."
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Resume esta noticia para un abogado: {article.title}. Contenido: {article.snippet[:2000]}"
        response = model.generate_content(prompt)
        article.ai_summary = response.text
        article.save()
        return True
    except Exception as e:
        return False


# Exports for safe imports from views
__all__ = [
    'analyze_legal_diff',
    'check_sutra_status',
    'fetch_latest_news',
    'generate_ai_summary',
    'generate_diff_html',
    'normalize_text',
]

def normalize_text(text):
    if not text: return ""
    return ''.join(c for c in unicodedata.normalize('NFD', text.lower()) if unicodedata.category(c) != 'Mn')