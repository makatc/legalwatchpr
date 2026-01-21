from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import HttpResponse
from .models import Bill, BillVersion, Event, Keyword, MonitoredMeasure, MonitoredCommission, NewsSource, Article, NewsPreset
from .utils import fetch_latest_news, generate_ai_summary, generate_diff_html, analyze_legal_diff, check_sutra_status
import datetime
import icalendar

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
    if NewsSource.objects.count() == 0:
        NewsSource.objects.create(name="Metro PR", url="https://www.metro.pr/arc/outboundfeeds/rss/", icon_class="fas fa-subway text-green-500")
    query = request.GET.get('q', '')
    articles = Article.objects.filter(title__icontains=query) if query else Article.objects.all()
    context = {
        'articles': articles[:100],
        'sources_count': NewsSource.objects.count(),
        'today_count': Article.objects.filter(published_at__date=datetime.date.today()).count()
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
def configuracion(request):
    if request.method == 'POST':
        if 'add_keyword' in request.POST:
            term = request.POST.get('term', '').strip()
            if term: Keyword.objects.get_or_create(term=term)
        elif 'add_measure' in request.POST:
            sutra_id = request.POST.get('sutra_id', '').strip()
            if sutra_id: MonitoredMeasure.objects.get_or_create(sutra_id=sutra_id)
        elif 'add_commission' in request.POST:
            name = request.POST.get('commission_name')
            if name: MonitoredCommission.objects.get_or_create(name=name)
        elif 'add_preset' in request.POST:
            name = request.POST.get('preset_name', '').strip()
            keywords = request.POST.get('preset_keywords', '').strip()
            if name and keywords:
                NewsPreset.objects.update_or_create(name=name, defaults={'keywords': keywords, 'is_active': True})
        return redirect('configuracion')

    context = {
        'keywords': Keyword.objects.all().order_by('term'),
        'measures': MonitoredMeasure.objects.all().order_by('sutra_id'),
        'comms': MonitoredCommission.objects.all().order_by('name'),
        'presets': NewsPreset.objects.all().order_by('name'),
        'available_commissions': sorted(AVAILABLE_COMMISSIONS),
    }
    return render(request, 'core/configuracion.html', context)

@login_required
def delete_item(request, item_type, item_id):
    model_map = {'keyword': Keyword, 'measure': MonitoredMeasure, 'commission': MonitoredCommission, 'preset': NewsPreset}
    if item_type in model_map:
        get_object_or_404(model_map[item_type], id=item_id).delete()
    return redirect('configuracion')

@login_required
def comparador(request, bill_id=None):
    if not bill_id:
        bills = Bill.objects.all().order_by('-last_updated')
        return render(request, 'core/comparador_selector.html', {'bills': bills})

    bill = get_object_or_404(Bill, id=bill_id)

    if request.method == 'POST' and request.FILES.get('pdf_file'):
        try:
            version_name = request.POST.get('version_name', 'Nueva Versión')
            pdf_file = request.FILES['pdf_file']
            BillVersion.objects.create(bill=bill, version_name=version_name, pdf_file=pdf_file)
            return redirect(request.path)
        except Exception as e: print(f"Error subiendo: {e}")

    versions = bill.versions.all().order_by('created_at')
    diff_html = ""
    ai_analysis = ""
    v1_id = request.GET.get('v1')
    v2_id = request.GET.get('v2')
    do_ai = request.GET.get('ai')

    if v1_id and v2_id:
        version1 = get_object_or_404(BillVersion, id=v1_id)
        version2 = get_object_or_404(BillVersion, id=v2_id)
        diff_html = generate_diff_html(version1.full_text, version2.full_text)
        if do_ai == 'true': ai_analysis = analyze_legal_diff(version1.full_text, version2.full_text)

    context = {
        'bill': bill, 'versions': versions, 'diff_html': diff_html, 'ai_analysis': ai_analysis,
        'v1_selected': int(v1_id) if v1_id else 0, 'v2_selected': int(v2_id) if v2_id else 0,
    }
    return render(request, 'core/comparador.html', context)

def calendar_feed(request):
    cal = icalendar.Calendar()
    cal.add('prodid', '-//LegalWatch AI//mxm.dk//')
    cal.add('version', '2.0')
    for event in Event.objects.all():
        ical_event = icalendar.Event()
        ical_event.add('summary', event.title)
        ical_event.add('dtstart', event.date)
        ical_event.add('description', event.description)
        if event.location: ical_event.add('location', event.location)
        cal.add_component(ical_event)
    return HttpResponse(cal.to_ical(), content_type="text/calendar")

# --- FUNCIÓN DE SALIDA ---
def logout_view(request):
    logout(request)
    return redirect('login')