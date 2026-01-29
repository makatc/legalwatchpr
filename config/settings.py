from pathlib import Path
import os
from dotenv import load_dotenv

# Resolve BASE_DIR from central resolver when available; fall back to file layout
try:
    from core.utils.paths import PROJECT_ROOT as BASE_DIR  # type: ignore
except Exception:
    BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env at project root
load_dotenv(str(BASE_DIR / '.env'))

# Expose API keys to Django settings (fallback from .env)
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Versión de la aplicación
VERSION = '1.1'

# --- SEGURIDAD ---
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-dev-key-change-in-prod')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

# --- APLICACIONES INSTALADAS ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_apscheduler',
    'core',
    'django.contrib.postgres',
    'rest_framework',  # Agregado explícitamente
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.security.RateLimitMiddleware',
    'core.middleware.security.SecurityHeadersMiddleware',
    'core.middleware.security.RequestValidationMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# --- BASE DE DATOS ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'legalwatchpr_db'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),  # Seguro por defecto
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# --- VALIDACIÓN DE CONTRASEÑAS ---
AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]

# --- IDIOMA Y ZONA HORARIA ---
LANGUAGE_CODE = 'es-us'
TIME_ZONE = 'America/Puerto_Rico'
USE_I18N = True
USE_TZ = True

# --- ARCHIVOS ESTÁTICOS ---
STATIC_URL = 'static/'
STATIC_ROOT = str(BASE_DIR / 'static')

# --- MEDIA ---
MEDIA_URL = '/media/'
MEDIA_ROOT = str(BASE_DIR / 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- LOGIN/LOGOUT ---
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'
LOGIN_URL = 'login'

# --- SEGURIDAD ---
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Rate limiting
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_SKIP_PATHS = ['/admin/', '/static/', '/media/']
MAX_REQUEST_SIZE = 10 * 1024 * 1024

# --- EMBEDDINGS ---
EMBEDDING_PROVIDER = 'sentence_transformers'
EMBEDDING_MODEL = 'paraphrase-multilingual-MiniLM-L12-v2'
EMBEDDING_DIMENSION = 384