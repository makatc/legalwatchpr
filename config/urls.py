from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # --- ESTA LÍNEA FALTABA ---
    # Esto activa el login y el logout automáticos de Django
    path('accounts/', include('django.contrib.auth.urls')),
    
    # Rutas de tu aplicación principal
    path('', include('core.urls')),
]