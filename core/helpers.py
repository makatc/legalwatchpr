import os
import logging
import difflib
from typing import Dict, List, Any
from pathlib import Path

import google.generativeai as genai
from django.conf import settings
from google.api_core.exceptions import ResourceExhausted, PermissionDenied

# Config logger
logger = logging.getLogger(__name__)

# Configure genai with API key from Django settings when available
if getattr(settings, "GOOGLE_API_KEY", None):
    genai.configure(api_key=settings.GOOGLE_API_KEY)

# MODELO SELECCIONADO (Basado en tu lista disponible)
MODEL_NAME = 'gemini-2.0-flash'

def normalize_text(text: str) -> str:
    """Normalize text for comparison/search."""
    if not text: return ""
    return " ".join(text.split()).strip()

def generate_diff_html(text1: str, text2: str) -> str:
    """Produce an HTML visual diff between two texts."""
    a_lines = (text1 or "").splitlines()
    b_lines = (text2 or "").splitlines()
    return difflib.HtmlDiff(wrapcolumn=80).make_file(a_lines, b_lines, context=True, numlines=3)

def analyze_legal_diff(text_old: str, text_new: str) -> Dict[str, Any]:
    """Analyze differences between two legal texts."""
    t1 = normalize_text(text_old)
    t2 = normalize_text(text_new)
    sm = difflib.SequenceMatcher(a=t1, b=t2)
    
    added, removed, changed = [], [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "insert": added.append({"text": t2[j1:j2], "pos": j1})
        elif tag == "delete": removed.append({"text": t1[i1:i2], "pos": i1})
        elif tag == "replace": changed.append({"from": t1[i1:i2], "to": t2[j1:j2], "pos_from": i1})

    return {
        "added": added, "removed": removed, "changed": changed,
        "html": generate_diff_html(text_old, text_new),
        "summary": {"added_count": len(added), "removed_count": len(removed), "changed_count": len(changed)},
    }

def check_sutra_status(measure_id):
    """Check the status of a measure on SUTRA."""
    import requests, urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    clean_id = str(measure_id).lower().replace("p. de la c.", "pc").replace(" ", "").replace(".", "")
    url = f"https://sutra.oslpr.org/osl/es/medidas/{clean_id}"
    try:
        res = requests.get(url, timeout=10, verify=False, headers={'User-Agent': 'Mozilla/5.0'})
        return (res.status_code == 200, "En línea" if res.status_code == 200 else f"Error {res.status_code}")
    except Exception as e:
        return (False, str(e))

def fetch_latest_news(limit: int = 10):
    from core.utils import sync_all_rss_sources
    return sync_all_rss_sources(max_entries=limit)

def generate_ai_summary(article_id):
    """Generate an AI summary using the configured Gemini model."""
    from core.models import Article
    try:
        article = Article.objects.get(id=article_id)
        if not getattr(settings, "GOOGLE_API_KEY", None): return "Error: API Key missing."
        
        model = genai.GenerativeModel(MODEL_NAME)
        prompt = f"Resume esta noticia para un abogado: {article.title}. Contenido: {article.snippet[:2000]}"
        
        response = model.generate_content(prompt)
        article.ai_summary = getattr(response, 'text', str(response))
        article.save()
        return True
    except Exception as e:
        logger.error(f"AI Summary Error: {e}")
        return False

def analyze_bill_relevance(bill):
    """Get relevance score using Gemini."""
    try:
        if not getattr(settings, "GOOGLE_API_KEY", None): return {"score": 0, "analysis": "API key missing"}
        
        # Skip if already analyzed
        if getattr(bill, 'ai_score', 0): 
            return {"score": bill.ai_score, "analysis": bill.ai_analysis, "skipped": True}

        model = genai.GenerativeModel(MODEL_NAME)
        prompt = (f"Analyze this Puerto Rico legislative measure: {bill.title}. "
                  "Return ONLY a JSON object with keys: 'score' (int 1-10) and 'reason' (string).")
        
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        
        import json
        data = json.loads(response.text)
        return {"score": int(data.get('score', 0)), "analysis": data.get('reason', '')[:500]}
    except Exception as e:
        logger.error(f"Bill Analysis Error: {e}")
        return {"score": 0, "analysis": "API Error"}

__all__ = ["analyze_legal_diff", "check_sutra_status", "fetch_latest_news", 
           "generate_ai_summary", "analyze_bill_relevance", "generate_diff_html", "normalize_text"]