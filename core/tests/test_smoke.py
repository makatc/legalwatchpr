import pytest
from django.urls import reverse

@pytest.mark.django_db
def test_login_page_loads(client):
    """Verifica que la página de login sea accesible."""
    url = reverse('login')
    response = client.get(url, HTTP_USER_AGENT='Mozilla/5.0 (SmokeTest)')
    assert response.status_code == 200
    assert "Iniciar Sesión" in response.content.decode('utf-8')

@pytest.mark.django_db
def test_dashboard_requires_login(client):
    """Verifica que el dashboard redirija a login si no hay sesión."""
    url = reverse('dashboard')
    response = client.get(url, HTTP_USER_AGENT='Mozilla/5.0 (SmokeTest)')
    assert response.status_code == 302
    assert "/login/" in response.url

@pytest.mark.django_db
def test_home_redirects_to_login_or_dashboard(client):
    """Verifica que la raíz redireccione correctamente."""
    url = reverse('home')
    response = client.get(url, HTTP_USER_AGENT='Mozilla/5.0 (SmokeTest)')
    # Debería redirigir a login ya que dashboard tiene @login_required
    assert response.status_code == 302

@pytest.mark.django_db
def test_noticias_requires_login(client):
    """Verifica protección de ruta de noticias."""
    url = reverse('noticias')
    response = client.get(url, HTTP_USER_AGENT='Mozilla/5.0 (SmokeTest)')
    assert response.status_code == 302

@pytest.mark.django_db
def test_configuracion_requires_login(client):
    """Verifica protección de ruta de configuración."""
    url = reverse('configuracion')
    response = client.get(url, HTTP_USER_AGENT='Mozilla/5.0 (SmokeTest)')
    assert response.status_code == 302

