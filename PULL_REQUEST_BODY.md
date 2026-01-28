Resumen
-------
Esta PR realiza una reestructura segura mínima para hacer el proyecto independiente del directorio de trabajo (CWD) y más robusto en cuanto a imports y rutas.

Objetivos principales
--------------------
- Resolver `PROJECT_ROOT` de forma centralizada (`core.utils.paths`) y exponer `CONFIG_DIR`, `SQL_DIR`, `SCRIPTS_DIR`, `TEMPLATES_DIR`, `STATIC_DIR`.
- Hacer que `core/` y `services/` sean paquetes estables y eliminar hacks de `sys.path` en scripts/tests.
- Usar imports perezosos para dependencias pesadas (ML, PDF/DOCX) y evitar fallos en import-time.
- Alinear `config/settings.py` con el resolver de root y normalizar rutas de `STATIC_ROOT`/`MEDIA_ROOT`.
- Añadir comandos de management seguros: `create_hnsw_index` y `run_scheduler`.
- Añadir checks y pruebas de humo (`tools/smoke_check.py`, `test_smoke_project_root.py`).

Cambios clave (archivos)
------------------------
- `core/utils/paths.py`, `core/utils/__init__.py`  : resolver central de rutas.
- `services/__init__.py`                            : lazy-load para evitar ciclos de import.
- `config/settings.py`                             : usar `PROJECT_ROOT` cuando sea posible.
- `scripts/add_and_test_ps0979.py`, `test_*.py`    : reemplazo de `sys.path` hacks por detección robusta del root.
- `core/management/commands/create_hnsw_index.py`  : ejecuta `sql/create_hnsw_index.sql` con confirmación.
- `core/management/commands/run_scheduler.py`      : plantilla para iniciar scheduler (requiere `--run`).
- `tools/smoke_check.py`, `test_smoke_project_root.py`: verificación mínima de entorno.
- `core/models.py`, `services/embedding_service.py`: cargas perezosas de `pypdf`, `docx`, `sentence_transformers`.

Cómo probar (local)
-------------------
Desde la raíz del repo:

```powershell
git fetch origin
git checkout refactor/safe-structure
python -m compileall .
python tools/smoke_check.py    # valida detección de rutas y import básico de settings
python -m pytest -q           # corre la suite de tests (requiere dependencias y DB configurada)
```

Notas sobre entorno y dependencias
---------------------------------
- El repositorio requiere varias dependencias opcionales (p. ej. `sentence_transformers`, `pypdf`, `python-docx`, `icalendar`, `django_apscheduler`) para todas las funcionalidades. El `smoke_check` y tests toleran su ausencia y emiten warnings.
- Si tu CI no instala todas las dependencias, la suite de tests puede necesitar ajustes en la matrix para instalar extras.

Checklist (commits)
--------------------
1. Add project root path resolver
2. Fix file paths to use PROJECT_ROOT and add smoke check
3. Normalize imports: lazy-load services to avoid circular imports
4. Replace sys.path hacks with robust root detection; add smoke test
5. Add management commands and finalize smoke_check robustness

Backwards compatibility
-----------------------
- `manage.py` queda en la raíz y sigue funcionando.
- Se añadieron shims y detección de root para mantener compatibilidad con scripts existentes; si algún script se rompe, configurar `LW_PROJECT_ROOT` como workaround.

Siguientes pasos recomendados
----------------------------
- Ejecutar CI y corregir fallos específicos de integración (DB/pgvector).  
- Considerar mover scripts a management commands o documented wrappers.  
- Añadir CI job que ejecute `tools/smoke_check.py` antes de tests.

Comentario
---------
Los cambios son de estructura/arranque y no alteran la lógica de negocio. Si desean que ajuste el PR description directamente en GitHub, puedo usar la API si se proporciona un token.
