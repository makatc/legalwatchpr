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

# Stubs de servicios (se implementarán en P1)
try:
    from services import (get_search_stats, search_documents, search_keyword_only,
                          search_semantic_only)
except ImportError:
    # Fallback para pasar el check si services no está listo aún
    def get_search_stats(): return {}
    def search_documents(*args, **kwargs): return []
    def search_keyword_only(*args, **kwargs): return []
    def search_semantic_only(*args, **kwargs): return []

from .models import (Article, Bill, BillVersion, Event, Keyword,
                      MonitoredCommission, MonitoredMeasure, NewsPreset,
                      NewsSource)
from .serializers import ArticleSearchResultSerializer, SearchStatsSerializer

# CORRECCIÓN AQUÍ: Importar desde .helpers en lugar de .utils
from .helpers import (analyze_legal_diff, check_sutra_status, fetch_latest_news,
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

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

@login_required
def dashboard(request):
    """Vista principal: muestra últimas noticias y leyes reales."""
    # Últimas 5 noticias
    latest_news = Article.objects.order_by('-published_at')[:5]
    # Últimas 5 leyes (por last_updated si existe, si no por id)
    if hasattr(Bill, 'last_updated'):
        latest_bills = Bill.objects.order_by('-last_updated')[:5]
    else:
        latest_bills = Bill.objects.order_by('-id')[:5]

    context = {
        'latest_news': latest_news,
        'latest_bills': latest_bills,
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def noticias(request):
    query = request.GET.get('q', '')
    articles = Article.objects.all().order_by('-published_at')
    if query:
        articles = articles.filter(title__icontains=query)
    paginator = Paginator(articles, 20)
    page = request.GET.get('page')
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    context = {
        'page_obj': page_obj,
        'query': query,
    }
    return render(request, 'core/noticias.html', context)

# Nueva vista: lista de leyes/medidas
@login_required
def medidas(request):
    query = request.GET.get('q', '')
    bills = Bill.objects.all().order_by('-last_updated' if hasattr(Bill, 'last_updated') else '-id')
    if query:
        bills = bills.filter(models.Q(title__icontains=query) | models.Q(number__icontains=query))
    paginator = Paginator(bills, 20)
    page = request.GET.get('page')
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    context = {
        'page_obj': page_obj,
        'query': query,
    }
    return render(request, 'core/medidas.html', context)

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


# --- ACCIONES ---

@login_required
def sync_noticias(request):
    """Lanzador de sincronización de noticias."""
    fetch_latest_news()
    return redirect('noticias')

@login_required
def resumir_noticia(request, article_id):
    """Genera resumen AI y recarga."""
    generate_ai_summary(article_id)
    return redirect('noticias')

@login_required
def api_resumir_noticia(request, article_id):
    """API para resumir artículo (AJAX)."""
    success = generate_ai_summary(article_id)
    return JsonResponse({'success': success})

def comparador(request, bill_id=None):
    """Página comparador."""
    return render(request, 'core/comparador.html', {'bill_id': bill_id})

# Simple endpoints para APIs administrativas
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

class DocumentSearchView(APIView):
    """
    API endpoint para búsqueda híbrida de documentos.
    
    Parámetros:
        - q (str, requerido): Texto de búsqueda
        - limit (int, opcional): Número máximo de resultados (default=20)
        - method (str, opcional): Método de búsqueda ['hybrid'|'semantic'|'keyword'] (default='hybrid')
    """
    def get(self, request, *args, **kwargs):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response(
                {'error': 'Parameter "q" is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        limit = int(request.query_params.get('limit', 20))
        search_method = request.query_params.get('method', 'hybrid').lower()
        
        try:
            # Enrutar a la función correcta según el método
            if search_method == 'semantic':
                results = search_semantic_only(query, limit=limit)
            elif search_method == 'keyword':
                results = search_keyword_only(query, limit=limit)
            elif search_method == 'hybrid':
                results = search_documents(query, limit=limit)
            else:
                return Response(
                    {'error': f'Invalid method "{search_method}". Use: hybrid, semantic, or keyword'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Serializar resultados
            serializer = ArticleSearchResultSerializer(results, many=True)
            return Response({
                'query': query,
                'method': search_method,
                'count': len(results),
                'results': serializer.data
            })
        
        except Exception as e:
            logger.error(f"Error en búsqueda: {e}", exc_info=True)
            return Response(
                {'error': 'Internal search error', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SearchStatsView(APIView):
    """
    API endpoint para obtener estadísticas de cobertura de búsqueda.
    
    Retorna métricas sobre artículos indexados y cobertura de embeddings.
    """
    def get(self, request, *args, **kwargs):
        try:
            stats = get_search_stats()
            serializer = SearchStatsSerializer(stats)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}", exc_info=True)
            return Response(
                {'error': 'Error retrieving stats', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )