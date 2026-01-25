Purpose
-------
This file gives an AI coding agent the minimal repository-specific knowledge to be productive quickly. Focus on "where things live", "how data flows", and the exact developer commands used by this project.

Big picture
-----------
- This is a Django project (see `manage.py` and `config/`) that indexes news/articles and supports hybrid vector+SQL search.
- Major components:
  - Django app: `core/` — models, API views, serializers, management commands, scheduler and scrapers.
  - Vector services: `services/embedding_service.py` and `services/hybrid_search.py` — embedding generation and hybrid search logic.
  - SQL helpers: `sql/create_hnsw_index.sql` for HNSW index creation; migrations add `pgvector`/embedding fields and triggers.

Key files to read first
-----------------------
- `manage.py` — standard Django entrypoint.
- `config/settings.py` — settings, installed apps, DB configuration.
- `core/models.py` — domain models (articles, sources, presets) and fields introduced by migrations (embedding/search fields).
- `services/embedding_service.py` — where embeddings are created/normalized; change here if using a different provider.
- `services/hybrid_search.py` — search ranking combining pgvector and Postgres full-text/search vectors.
- `sql/create_hnsw_index.sql` — HNSW index creation for pgvector + pgvector_hnsw.
- `core/management/commands/` — custom CLI tasks (useful for automation and tests).

Important patterns & conventions
-------------------------------
- Embeddings are stored on model fields (see migrations: `0021_article_embedding.py` etc.). Update migrations when adding persistent fields.
- Hybrid search combines a vector similarity step and a Postgres search vector/threshold. See `services/hybrid_search.py` for exact SQL/ORM patterns to preserve.
- Background work is orchestrated by scheduler and custom management commands in `core/` (look at `scheduler.py` and `management/commands`).
- Tests: lightweight pytest-style tests exist at repo root (`test_*.py`). They assume Django settings from `config/` and a configured test DB.

Developer workflows (commands)
------------------------------
- Install Python deps:
  - `python -m pip install -r requirements.txt`
- Setup Postgres + pgvector on Windows: follow INSTALL_PGVECTOR_WINDOWS.md and the PowerShell helpers (`*.ps1`).
- Run migrations: `python manage.py migrate`
- Create HNSW index (when DB ready): run `psql` with `sql/create_hnsw_index.sql` or use provided helper scripts.
- Run tests: project uses pytest-style tests; run `pytest -q` or `python -m pytest -q` from repo root.
- Start local server: `python manage.py runserver`

Integration points & external dependencies
----------------------------------------
- Postgres with `pgvector` extension and optional HNSW index (see `MIGRATION` files and `sql/create_hnsw_index.sql`).
- Embedding provider: implemented in `services/embedding_service.py` — replace or mock for tests.
- There are several platform-specific install scripts (PowerShell) in the repo root — use them on Windows.

When editing code
------------------
- If changing embeddings or search logic, update/inspect related migrations and `core/models.py` to keep DB schema consistent.
- Preserve the hybrid search SQL patterns in `services/hybrid_search.py` — tests rely on its behavior.
- Add or update management commands for scheduled/background tasks rather than adding ad-hoc cron-like scripts.

Quick examples (where to change things)
-------------------------------------
- To change embedding provider: edit `services/embedding_service.py` and adapt tests that mock embeddings.
- To tune search ranking: edit `services/hybrid_search.py` and the SQL in `sql/create_hnsw_index.sql` for index parameters.
- To add a background job: add a `core/management/commands/<name>.py` and hook it into `core/scheduler.py`.

If unsure, ask the maintainer for DB credentials, or run the local PowerShell install scripts to reproduce the developer environment on Windows.

Feedback
--------
If any section is unclear or you want more examples (tests, management commands, or migration details), tell me which area to expand.
