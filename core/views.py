import datetime
import json
import logging
import re
import icalendar

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from services import (get_search_stats, search_documents, search_keyword_only,
                      search_semantic_only)

from .models import (Article, Bill, BillVersion, Event, Keyword,
                      MonitoredCommission, MonitoredMeasure, NewsPreset,
                      NewsSource)
from .serializers import ArticleSearchResultSerializer, SearchStatsSerializer
from .utils import (analyze_legal_diff, check_sutra_status, fetch_latest_news,
                    generate_ai_summary, generate_diff_html, normalize_text)

logger = logging.getLogger(__name__)

# Lista maestra de comisiones para Puerto Rico
AVAILABLE_COMMISSIONS = [
    "Agricultura", "Asuntos del Consumidor", "Asuntos de la Mujer", "Asuntos Internos",
    "Asuntos Laborales", "Asuntos Municipales", "Autonomía Municipal", "Bienestar Social",
    "Calendario y Reglas Especiales", "Cooperativismo", "Desarrollo Económico",
    "Desarrollo Integrado de la Región Sur", "Desarrollo Integrado de la Región Oeste",
    "Desarrollo Integrado de la Región Norte", "Desarrollo Integrado de la Región Este",
    "Desarrollo Integrado de la Región Centro", "Educación, Arte y Cultura", "Energía",
    "Ética", "Hacienda y Presupuesto", "Impacto Comunitario", "Innovación, Telecomunicaciones",
    "Jurídico", "Juventud", "Nombramientos", "Pequeños y Medianos Negocios",
    "Preparación, Reconstrucción y Reorganización", "Probidad y Ética Gubernamental",
    "Proyectos Estratégicos y Energía", "Recursos Naturales y Ambientales",
    "Recreación y Deportes", "Relaciones Federales", "Salud", "Seguridad Pública",
    "Sistemas de Retiro", "Transportación e Infraestructura", "Turismo", "Vivienda y Desarrollo Urbano"
]

@login_required
def dashboard(request):
    """Vista principal: Carga medidas, keywords y comisiones para SUTRA"""
    monitored_data = []
    measures = MonitoredMeasure.objects.filter(is_active=True)
    for m in measures:
        is_online, status_msg = check_sutra_status(m.sutra_id)
        monitored_data.append({
            'id': m.id,
            'sutra_id': m.sutra_id,
            'is_online': is_online,
            'status_msg': status_msg,
            'added_at': m.added_at
        })

    context = {
        'total_bills': Bill.objects.count(),
        'recent_bills': Bill.objects.all().order_by('-last_updated')[:5],
        'recent_events': Event.objects.all().order_by('-date')[:5],
        'monitored_measures': monitored_data,
        'keywords': Keyword.objects.all().order_by('term'),
        'comms': MonitoredCommission.objects.filter(is_active=True).order_by('name'),
        'available_commissions': sorted(AVAILABLE_COMMISSIONS),
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def noticias(request):
    query = request.GET.get('q', '')
    search_method = request.GET.get('method', 'hybrid')
    
    if query:
        try:
            if search_method == 'semantic':
                search_results = search_semantic_only(query, limit=100)
            elif search_method == 'keyword':
                search_results = search_keyword_only(query, limit=100)
            else:
                search_results = search_documents(query, limit=100)
            
            article_ids = [r['id'] for r in search_results]
            articles = Article.objects.filter(id__in=article_ids)
        except Exception as e:
            logger.error(f"Error en búsqueda: {e}")
            articles = Article.objects.filter(title__icontains=query)[:100]
    else:
        articles = Article.objects.all().order_by('-published_at')[:100]
    
    context = {
        'articles': articles,
        'query': query,
        'presets': NewsPreset.objects.all(),
        'sources': NewsSource.objects.all()
    }
    return render(request, 'core/noticias.html', context)

@login_required
def dashboard_configuracion(request):
    """Maneja el guardado de configuración de SUTRA"""
    if request.method == 'POST':
        if 'add_measure' in request.POST:
            m_id = request.POST.get('measure_id', '').strip()
            if m_id: MonitoredMeasure.objects.get_or_create(sutra_id=m_id, is_active=True)
        elif 'add_commission' in request.POST:
            c_name = request.POST.get('commission_name', '').strip()
            if c_name: MonitoredCommission.objects.get_or_create(name=c_name, is_active=True)
        elif 'add_keyword' in request.POST:
            term = request.POST.get('keyword', '').strip()
            if term: Keyword.objects.get_or_create(term=term)
        return redirect('dashboard_configuracion')

    context = {
        'keywords': Keyword.objects.all().order_by('term'),
        'monitored_measures': MonitoredMeasure.objects.all().order_by('-added_at'),
        'monitored_commissions': MonitoredCommission.objects.filter(is_active=True),
        'available_commissions': sorted(AVAILABLE_COMMISSIONS),
    }
    return render(request, 'core/dashboard_configuracion.html', context)

@login_required
def delete_item(request, item_type, item_id):
    """Borra ítems y redirige dinámicamente"""
    model_map = {'keyword': Keyword, 'measure': MonitoredMeasure, 'commission': MonitoredCommission, 'preset': NewsPreset}
    if item_type in model_map:
        get_object_or_404(model_map[item_type], id=item_id).delete()
    
    if item_type in ['keyword', 'measure', 'commission']:
        return redirect('dashboard_configuracion')
    return redirect('configuracion')

@login_required
def configuracion(request):
    """Configuración para Noticias"""
    context = {
        'sources': NewsSource.objects.all().order_by('name'),
        'presets': NewsPreset.objects.all().order_by('name'),
    }
    return render(request, 'core/configuracion.html', context)

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

# --- MANTENIMIENTO DE CALENDARIO ---
@login_required
def calendario(request):
    context = {'recent_events': Event.objects.all().order_by('date')}
    return render(request, 'core/calendario.html', context)

def calendar_feed(request):
    cal = icalendar.Calendar()
    for event in Event.objects.all():
        ical_event = icalendar.Event()
        ical_event.add('summary', event.title)
        ical_event.add('dtstart', event.date)
        cal.add_component(ical_event)
    return HttpResponse(cal.to_ical(), content_type="text/calendar")


# --- STUBS PARA RESOLVER RUTAS (mínimos para `manage.py check`) ---
def sync_noticias(request):
    """Lanzador de sincronización de noticias (stub)."""
    # En producción esto lanzaría tareas o management commands
    return JsonResponse({'ok': True, 'msg': 'sync initiated'})


def resumir_noticia(request, article_id):
    """Vista que muestra un resumen (stub)."""
    summary = generate_ai_summary(article_id)
    return HttpResponse(summary)


def api_resumir_noticia(request, article_id):
    """API para resumir artículo (stub)."""
    summary = generate_ai_summary(article_id)
    return JsonResponse({'id': article_id, 'summary': summary})


def comparador(request, bill_id=None):
    """Página comparador (stub)."""
    return render(request, 'core/comparador.html', {'bill_id': bill_id})


# Simple endpoints para APIs administrativas (stubs)
def api_add_source(request):
    return JsonResponse({'ok': True})


def api_delete_source(request, source_id):
    return JsonResponse({'ok': True, 'deleted': source_id})


def api_toggle_source(request, source_id):
    return JsonResponse({'ok': True, 'toggled': source_id})


def api_add_preset(request):
    return JsonResponse({'ok': True})


def api_delete_preset(request, preset_id):
    return JsonResponse({'ok': True, 'deleted': preset_id})


def api_toggle_preset(request, preset_id):
    return JsonResponse({'ok': True, 'toggled': preset_id})


def generate_keywords_ai(request):
    return JsonResponse({'ok': True})


def api_save_profile(request):
    return JsonResponse({'ok': True})


def api_save_webhook(request):
    return JsonResponse({'ok': True})


from rest_framework.views import APIView


class DocumentSearchView(APIView):
    def get(self, request, *args, **kwargs):
        return Response({'results': []})


class SearchStatsView(APIView):
    def get(self, request, *args, **kwargs):
        return Response({'stats': {}})