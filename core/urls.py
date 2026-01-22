from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # --- RUTAS DE ACCESO (LOGIN/LOGOUT) ---
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),

    # --- RUTAS DEL SISTEMA ---
    path('', views.dashboard, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('calendario/', views.calendario, name='calendario'),
    path('noticias/', views.noticias, name='noticias'),
    path('sync-noticias/', views.sync_noticias, name='sync_noticias'),
    path('resumir/<int:article_id>/', views.resumir_noticia, name='resumir_noticia'),
    path('api/resumir/<int:article_id>/', views.api_resumir_noticia, name='api_resumir_noticia'),
    path('configuracion/', views.configuracion, name='configuracion'),
    path('delete/<str:item_type>/<int:item_id>/', views.delete_item, name='delete_item'),
    path('calendar/feed/', views.calendar_feed, name='calendar_feed'),
    path('comparador/', views.comparador, name='comparador_home'),
    path('comparador/<int:bill_id>/', views.comparador, name='comparador'),
    
    # --- API ENDPOINTS ---
    path('api/sources/add/', views.api_add_source, name='api_add_source'),
    path('api/sources/<int:source_id>/delete/', views.api_delete_source, name='api_delete_source'),
    path('api/sources/<int:source_id>/toggle/', views.api_toggle_source, name='api_toggle_source'),
    path('api/presets/add/', views.api_add_preset, name='api_add_preset'),
    path('api/presets/<int:preset_id>/delete/', views.api_delete_preset, name='api_delete_preset'),
    path('api/presets/<int:preset_id>/toggle/', views.api_toggle_preset, name='api_toggle_preset'),
]