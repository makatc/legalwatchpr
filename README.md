# LegalWatchPR 🇵🇷⚖️

**Plataforma de monitoreo legislativo y de noticias para Puerto Rico** con búsqueda híbrida (semántica + full-text) e inteligencia artificial.

---

## ✨ Funcionalidades

- **Monitoreo de noticias** — Sincronización automática de fuentes RSS de medios puertorriqueños
- **Búsqueda híbrida** — Combina búsqueda semántica (pgvector) con full-text de PostgreSQL usando Reciprocal Rank Fusion (RRF)
- **Resúmenes con IA** — Generación automática de resúmenes legales usando Google Gemini
- **Comparador legislativo** — Comparación visual de versiones de medidas legislativas (PDF/DOCX)
- **Monitoreo SUTRA** — Seguimiento de medidas y comisiones de la Asamblea Legislativa de PR
- **Calendario** — Agenda de eventos legislativos con feed iCal
- **Dashboard configurable** — Presets de búsqueda, webhooks, y gestión de fuentes

---

## 📁 Estructura del Proyecto

```
legalwatchpr/
├── config/                  # Configuración Django
│   ├── settings.py          # Settings principal
│   ├── urls.py              # URL raíz
│   ├── wsgi.py / asgi.py    # Entrypoints WSGI/ASGI
│   └── __init__.py
├── core/                    # Aplicación principal Django
│   ├── models.py            # Modelos (Article, Bill, NewsSource, etc.)
│   ├── views.py             # Vistas HTML + API endpoints
│   ├── urls.py              # Rutas de la aplicación
│   ├── admin.py             # Admin de Django
│   ├── helpers.py           # Funciones de IA (Gemini), diff legal
│   ├── scraper.py           # Scraper legislativo (SUTRA)
│   ├── scheduler.py         # Programador de tareas automáticas
│   ├── signals.py           # Señales (auto-embedding al guardar artículos)
│   ├── serializers.py       # Serializadores DRF
│   ├── notificaciones.py    # Sistema de notificaciones
│   ├── management/commands/ # Comandos de gestión Django
│   │   ├── ejecutar_robot.py
│   │   ├── run_news_bot.py
│   │   ├── servicio_continuo.py
│   │   ├── sync_bills.py
│   │   ├── generate_embeddings.py
│   │   ├── backfill_embeddings.py
│   │   ├── evaluate_search.py
│   │   ├── create_hnsw_index.py
│   │   ├── run_scheduler.py
│   │   └── probar_robot.py
│   ├── middleware/           # Middleware de seguridad
│   ├── templates/core/      # Templates HTML
│   ├── utils/               # Utilidades (paths, RSS sync, SUTRA sync)
│   └── static/img/          # Recursos estáticos
├── services/                # Capa de servicios
│   ├── embedding_service.py # Generación de embeddings (sentence-transformers)
│   ├── hybrid_search.py     # Motor de búsqueda híbrida (RRF)
│   └── metrics.py           # Métricas de búsqueda
├── tools/                   # Herramientas de desarrollo
│   └── smoke_check.py       # Verificación rápida del proyecto
├── sql/                     # Scripts SQL
│   └── create_hnsw_index.sql
├── scripts/                 # Scripts auxiliares
├── manage.py                # Entrypoint Django
├── requirements.txt         # Dependencias Python
├── .env.example             # Plantilla de variables de entorno
└── .github/workflows/ci.yml # CI con GitHub Actions
```

---

## 🛠️ Requisitos

- **Python** 3.11+
- **PostgreSQL** 15+ con extensiones:
  - `pgvector` — para búsqueda semántica
  - `unaccent` — para normalización de texto
- **API Key de Google** (Gemini) — para resúmenes IA

---

## 🚀 Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/legalwatchpr.git
cd legalwatchpr
```

### 2. Crear entorno virtual e instalar dependencias
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 3. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con tus credenciales
```

### 4. Configurar PostgreSQL
```sql
CREATE DATABASE legalwatchpr_db;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS unaccent;
```

### 5. Ejecutar migraciones
```bash
python manage.py migrate
```

### 6. Crear superusuario
```bash
python manage.py createsuperuser
```

### 7. Iniciar servidor
```bash
python manage.py runserver
```

---

## ⚙️ Configuración (`.env`)

| Variable | Descripción | Default |
|---|---|---|
| `DB_NAME` | Nombre de la base de datos | `legalwatchpr_db` |
| `DB_USER` | Usuario PostgreSQL | `postgres` |
| `DB_PASSWORD` | Contraseña PostgreSQL | — |
| `DB_HOST` | Host de PostgreSQL | `localhost` |
| `DB_PORT` | Puerto de PostgreSQL | `5432` |
| `SECRET_KEY` | Clave secreta de Django | — |
| `DEBUG` | Modo debug | `True` |
| `ALLOWED_HOSTS` | Hosts permitidos | `*` |
| `GOOGLE_API_KEY` | API Key de Google Gemini | — |
| `GROQ_API_KEY` | API Key de Groq | — |

---

## 🤖 Comandos de Gestión

```bash
# Servicio continuo de monitoreo
python manage.py servicio_continuo

# Bot de noticias (sincronización RSS)
python manage.py run_news_bot

# Sincronizar medidas legislativas
python manage.py sync_bills

# Generar embeddings para artículos existentes
python manage.py generate_embeddings

# Backfill de embeddings faltantes
python manage.py backfill_embeddings

# Crear índice HNSW para búsqueda semántica
python manage.py create_hnsw_index

# Evaluar calidad de búsqueda
python manage.py evaluate_search

# Verificación rápida del proyecto
python tools/smoke_check.py
```

---

## 🔍 API Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/search/?q=texto` | Búsqueda híbrida de documentos |
| `GET` | `/api/search/stats/` | Estadísticas de cobertura de búsqueda |
| `POST` | `/api/resumir/<id>/` | Generar resumen IA de un artículo |
| `POST` | `/api/generate-keywords/` | Generar keywords con IA |
| `POST` | `/api/sources/add/` | Agregar fuente de noticias |
| `POST` | `/api/presets/add/` | Agregar preset de búsqueda |
| `POST` | `/api/save-profile/` | Guardar perfil de usuario |
| `POST` | `/api/save-webhook/` | Configurar webhook |

---

## 🧪 Tests

```bash
# Ejecutar todos los tests
pytest -q

# Verificación básica de estructura
python tools/smoke_check.py
```

---

## 🏗️ Stack Tecnológico

- **Backend**: Django 4.2+ / Django REST Framework
- **Base de Datos**: PostgreSQL 15+ con pgvector
- **IA**: Google Gemini 2.0 Flash (resúmenes, análisis)
- **Embeddings**: sentence-transformers (`paraphrase-multilingual-MiniLM-L12-v2`)
- **Scraping**: BeautifulSoup4, feedparser
- **Scheduler**: APScheduler / django-apscheduler
