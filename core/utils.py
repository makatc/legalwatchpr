import os
import logging
import difflib
from typing import Dict, List, Any

from dotenv import load_dotenv
import google.generativeai as genai
from django.conf import settings
from google.api_core.exceptions import ResourceExhausted, PermissionDenied

# Load environment from the absolute path provided (keeps backward compatibility)
load_dotenv(r"C:\Users\becof\vs\legalwatchpr\.env")

# Configure genai with API key from Django settings when available
if getattr(settings, "GOOGLE_API_KEY", None):
    genai.configure(api_key=settings.GOOGLE_API_KEY)

logger = logging.getLogger(__name__)


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison/search: collapse whitespace, strip, lowercase.
    """
    if not text:
        return ""
    return " ".join(text.split()).strip()


def generate_diff_html(text1: str, text2: str) -> str:
    """
    Produce an HTML visual diff between two texts.
    """
    a_lines = (text1 or "").splitlines()
    b_lines = (text2 or "").splitlines()
    html = difflib.HtmlDiff(wrapcolumn=80).make_file(a_lines, b_lines, context=True, numlines=3)
    return html


def analyze_legal_diff(text_old: str, text_new: str) -> Dict[str, Any]:
    """
    Analyze differences between two legal texts and return a structured summary plus HTML.
    """
    t1 = normalize_text(text_old)
    t2 = normalize_text(text_new)

    # Use unified opcode analysis for fine-grained changes
    sm = difflib.SequenceMatcher(a=t1, b=t2)
    opcodes = sm.get_opcodes()

    added: List[Dict[str, str]] = []
    removed: List[Dict[str, str]] = []
    changed: List[Dict[str, str]] = []

    for tag, i1, i2, j1, j2 in opcodes:
        a_seg = t1[i1:i2]
        b_seg = t2[j1:j2]
        if tag == "insert":
            added.append({"text": b_seg, "pos": j1})
        elif tag == "delete":
            removed.append({"text": a_seg, "pos": i1})
        elif tag == "replace":
            changed.append({"from": a_seg, "to": b_seg, "pos_from": i1, "pos_to": j1})

    html = generate_diff_html(text_old, text_new)

    return {
        "added": added,
        "removed": removed,
        "changed": changed,
        "html": html,
        "summary": {
            "added_count": len(added),
            "removed_count": len(removed),
            "changed_count": len(changed),
        },
    }


def check_sutra_status(measure_id):
    """
    Check the status of a measure on SUTRA OSLPR system.
    """
    import requests
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    clean_id = str(measure_id).lower().replace("p. de la c.", "pc").replace(" ", "").replace(".", "")
    url = f"https://sutra.oslpr.org/osl/es/medidas/{clean_id}"
    try:
        res = requests.get(url, timeout=10, verify=False, headers={'User-Agent': 'Mozilla/5.0'})
        return (res.status_code == 200, "En línea" if res.status_code == 200 else f"Error {res.status_code}")
    except Exception as e:
        return (False, str(e))


def fetch_latest_news(limit: int = 10):
    """
    Fetch latest news/articles by syncing RSS sources.
    """
    from app.modules.noticias.scraper import sync_all_rss_sources
    return sync_all_rss_sources(max_entries=10)


def generate_ai_summary(article_id):
    """
    Generate an AI summary for an article using Gemini API.
    """
    from core.models import Article
    try:
        article = Article.objects.get(id=article_id)
        if not getattr(settings, "GOOGLE_API_KEY", None):
            return "Error: API Key missing."
        model = genai.GenerativeModel('gemini-3-flash')
        prompt = f"Resume esta noticia para un abogado: {article.title}. Contenido: {article.snippet[:2000]}"
        try:
            response = model.generate_content(prompt)
        except ResourceExhausted:
            logger.warning("generate_ai_summary: quota exhausted")
            return "Error: quota exhausted"
        article.ai_summary = getattr(response, 'text', str(response))
        article.save()
        return True
    except Exception:
        return False


# Expose functions at module level
__all__ = [
    "analyze_legal_diff",
    "check_sutra_status",
    "fetch_latest_news",
    "generate_ai_summary",
    "analyze_bill_relevance",
    "generate_diff_html",
    "normalize_text",
]


def analyze_bill_relevance(bill):
    """
    Send bill title and number to Gemini to get a relevance score and short analysis.
    Returns {'score': int, 'analysis': str} or raises/returns None on failure.
    """
    try:
        if not getattr(settings, "GOOGLE_API_KEY", None):
            logger.warning("GOOGLE_API_KEY not configured for analyze_bill_relevance")
            return {"score": 0, "analysis": "API key missing"}

        # Skip external API call if already analyzed
        try:
            existing_score = int(getattr(bill, 'ai_score', 0) or 0)
        except Exception:
            existing_score = 0
        if existing_score > 0:
            return {"score": existing_score, "analysis": getattr(bill, 'ai_analysis', ''), "skipped": True}

        # Use Gemini 3 Flash explicitly
        model = genai.GenerativeModel('gemini-3-flash')

        title = getattr(bill, 'title', '')
        number = getattr(bill, 'number', '')
        prompt = (
            f"Analyze this Puerto Rico legislative measure: {title}. "
            "Return ONLY a JSON object with two keys: 'score' (integer 1-10) and 'reason' (max 2 sentences)."
        )

        generation_config = {
            "response_mime_type": "application/json"
        }

        print(f"--- 🧠 Calling Gemini 3 Flash for: {number} ---")

        try:
            response = model.generate_content(prompt, generation_config=generation_config)
            text = response.text if hasattr(response, 'text') else str(response)
        except ResourceExhausted:
            logger.warning("analyze_bill_relevance: quota exhausted for %s", number)
            return {"score": 0, "analysis": "Quota exhausted", "skipped": False}
        except PermissionDenied as e:
            # Avoid printing full stack or sensitive details; log concise message and continue.
            logger.warning("analyze_bill_relevance permission denied for %s: %s", number, str(e))
            return {"score": 0, "analysis": "Permission denied - invalid API key", "skipped": False}

        # Try to parse JSON response
        import re
        import json
        try:
            data = json.loads(text)
            score = int(data.get('score', 0))
            analysis = data.get('reason', text)[:500]
        except (json.JSONDecodeError, ValueError, KeyError):
            # Fallback: try to extract a score (1-10) from the response
            m = re.search(r"(\\b[1-9]\\b|10)", text)
            score = int(m.group(0)) if m else 0
            analysis = " ".join(text.split())[:500]

        return {"score": score, "analysis": analysis}
    except Exception as e:
        # Log concise error without exc_info to avoid leaking sensitive details
        logger.error("analyze_bill_relevance unexpected error: %s", str(e))
        return {"score": 0, "analysis": "API Error"}
from app.modules.sutra.scheduler import scheduler_function