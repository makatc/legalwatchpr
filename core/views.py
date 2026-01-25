import datetime
import json
import logging
import icalendar
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

# Importación de servicios de búsqueda
from services import (get_search_stats, search_documents, search_keyword_only,
                      search_semantic_only)

from .models import (Article, Bill, BillVersion, Event, 
                     MonitoredCommission, MonitoredMeasure, NewsPreset,
                     NewsSource)
from .serializers import ArticleSearchResultSerializer, SearchStatsSerializer
from .utils import (analyze_legal_diff, check_sutra_status, fetch_latest_news,
                    generate_ai_summary, generate_diff_html)

logger = logging.getLogger(__name__)

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
    monitored_data = []
    measures = MonitoredMeasure.objects.all()
    for m in measures:
        is_online, status_msg = check_sutra_status(m.sutra_id)
        monitored_data.append({
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
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def calendario(request):
    feed_url = request.build_absolute_uri('/calendar/feed/')
    context = {'recent_events': Event.objects.all().order_by('date'), 'feed_url': feed_url}
    return render(request, 'core/calendario.html', context)

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
            articles_dict = {a.id: a for a in Article.objects.filter(id__in=article_ids)}
            articles = [articles_dict[aid] for aid in article_ids if aid in articles_dict]
            
            for article, result in zip(articles, search_results):
                article.search_score = result.get('rrf_score') or result.get('similarity') or result.get('rank_score')
        except Exception as e:
            logger.error(f"Error en búsqueda: {e}")
            articles = Article.objects.filter(title__icontains=query)[:100]
    else:
        articles = Article.objects.all().order_by('-published_at')[:100]
    
    context = {
        'articles': articles,
        'query': query,
        'search_method': search_method,
        'sources_count': NewsSource.objects.count(),
        'presets': NewsPreset.objects.all(),
        'sources': NewsSource.objects.all()
    }
    return render(request, 'core/noticias.html', context)

@login_required
def sync_noticias(request):
    fetch_latest_news()
    return redirect('noticias')

@login_required
def resumir_noticia(request, article_id):
    generate_ai_summary(article_id)
    return redirect('noticias')

@login_required
def api_resumir_noticia(request, article_id):
    success = generate_ai_summary(article_id)
    article = get_object_or_404(Article, id=article_id)
    return JsonResponse({'success': success, 'summary': article.ai_summary})

@login_required
def configuracion(request):
    context = {
        'sources': NewsSource.objects.all().order_by('name'),
        'presets': NewsPreset.objects.all().order_by('name'),
    }
    return render(request, 'core/configuracion.html', context)

@login_required
def dashboard_configuracion(request):
    context = {
        'monitored_measures': MonitoredMeasure.objects.all().order_by('-added_at'),
        'monitored_commissions': MonitoredCommission.objects.all().order_by('name'),
        'available_commissions': sorted(AVAILABLE_COMMISSIONS),
    }
    return render(request, 'core/dashboard_configuracion.html', context)

@login_required
def delete_item(request, item_type, item_id):
    model_map = {'measure': MonitoredMeasure, 'commission': MonitoredCommission, 'preset': NewsPreset}
    if item_type in model_map:
        get_object_or_404(model_map[item_type], id=item_id).delete()
    return redirect('configuracion')

def calendar_feed(request):
    cal = icalendar.Calendar()
    cal.add('prodid', '-//LegalWatch AI//')
    cal.add('version', '2.0')
    for event in Event.objects.all():
        ical_event = icalendar.Event()
        ical_event.add('summary', event.title)
        ical_event.add('dtstart', event.date)
        cal.add_component(ical_event)
    return HttpResponse(cal.to_ical(), content_type="text/calendar")

@login_required
def comparador(request, bill_id=None):
    if not bill_id:
        bills = Bill.objects.all().order_by('-last_updated')
        return render(request, 'core/comparador_selector.html', {'bills': bills})
    bill = get_object_or_404(Bill, id=bill_id)
    versions = bill.versions.all().order_by('created_at')
    return render(request, 'core/comparador.html', {'bill': bill, 'versions': versions})

@login_required
def generate_keywords_ai(request):
    return JsonResponse({'success': True, 'results': {}})

def logout_view(request):
    logout(request)
    return redirect('login')

# --- API ENDPOINTS (STUBS) ---
def api_add_source(request): return JsonResponse({'success': True})
def api_delete_source(request, source_id): return JsonResponse({'success': True})
def api_toggle_source(request, source_id): return JsonResponse({'success': True})
def api_add_preset(request): return JsonResponse({'success': True})
def api_delete_preset(request, preset_id): return JsonResponse({'success': True})
def api_toggle_preset(request, preset_id): return JsonResponse({'success': True})

class DocumentSearchView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request): return Response({'success': True, 'results': []})

class SearchStatsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request): return Response({'success': True, 'stats': {}})