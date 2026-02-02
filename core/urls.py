from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    # ==========================================
    # 🔐 AUTENTICACIÓN (Login/Logout)
    # ==========================================
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="core/login.html"),
        name="login",
    ),
    path("logout/", views.logout_view, name="logout"),
    # ==========================================
    # 🖥️ FRONTEND (Vistas HTML para el usuario)
    # ==========================================
    # Dashboard principal
    path("", views.dashboard, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path(
        "dashboard/configuracion/",
        views.dashboard_configuracion,
        name="dashboard_configuracion",
    ),
    # Módulo de Noticias
    path("noticias/", views.noticias, name="noticias"),
    path(
        "sync-noticias/", views.sync_noticias, name="sync_noticias"
    ),  # Botón manual de sync
    # Herramientas Legales (Comparador/Resumidor)
    path("comparador/", views.comparador, name="comparador_home"),
    path("comparador/<int:bill_id>/", views.comparador, name="comparador"),
    path("resumir/<int:article_id>/", views.resumir_noticia, name="resumir_noticia"),
    # Listado de leyes/proyectos
    path("medidas/", views.medidas, name="medidas"),
    # Utilidades (Calendario, Configuración, Borrado)
    path("calendario/", views.calendario, name="calendario"),
    path("calendar/feed/", views.calendar_feed, name="calendar_feed"),
    path("configuracion/", views.configuracion, name="configuracion"),
    path(
        "delete/<str:item_type>/<int:item_id>/", views.delete_item, name="delete_item"
    ),
    # ==========================================
    # 🤖 API ENDPOINTS (JSON para AJAX/React)
    # ==========================================
    # --- 🧠 Búsqueda Híbrida e IA (LO NUEVO - Tarea P1) ---
    path("api/search/", views.DocumentSearchView.as_view(), name="api_search"),
    path("api/search/stats/", views.SearchStatsView.as_view(), name="api_search_stats"),
    path(
        "api/resumir/<int:article_id>/",
        views.api_resumir_noticia,
        name="api_resumir_noticia",
    ),
    path(
        "api/generate-keywords/",
        views.generate_keywords_ai,
        name="generate_keywords_ai",
    ),
    # --- ⚙️ Gestión de Fuentes y Perfiles ---
    path("api/sources/add/", views.api_add_source, name="api_add_source"),
    path(
        "api/sources/<int:source_id>/delete/",
        views.api_delete_source,
        name="api_delete_source",
    ),
    path(
        "api/sources/<int:source_id>/toggle/",
        views.api_toggle_source,
        name="api_toggle_source",
    ),
    # --- 🏷️ Presets de Búsqueda ---
    path("api/presets/add/", views.api_add_preset, name="api_add_preset"),
    path(
        "api/presets/<int:preset_id>/delete/",
        views.api_delete_preset,
        name="api_delete_preset",
    ),
    path(
        "api/presets/<int:preset_id>/toggle/",
        views.api_toggle_preset,
        name="api_toggle_preset",
    ),
    # --- 💾 Configuración Usuario ---
    path("api/save-profile/", views.api_save_profile, name="api_save_profile"),
    path("api/save-webhook/", views.api_save_webhook, name="api_save_webhook"),
]
