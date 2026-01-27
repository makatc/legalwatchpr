Resumen de reestructura mínima

Cambios introducidos:
- Añadido `core/utils/paths.py` para resolver `PROJECT_ROOT` y rutas clave (`CONFIG_DIR`, `SQL_DIR`, `SCRIPTS_DIR`, `TEMPLATES_DIR`, `STATIC_DIR`).
- Normalizado `config/settings.py` para usar el resolver de proyecto cuando está disponible.
- Hecho `services` package lazy-load sus símbolos para evitar imports circulares.
- Reemplazados los arreglos frágiles de `sys.path` en scripts/tests por detección robusta de root; soporta `LW_PROJECT_ROOT`.
- Añadido `tools/smoke_check.py` y `test_smoke_project_root.py` para verificación básica.

Cómo usar (desarrollo)

1) Ejecutar el chequeo rápido desde la raíz del repo:

```powershell
python tools/smoke_check.py
```

2) Ejecutar tests (requiere entorno de Django y DB configurados):

```powershell
python -m pytest -q
```

Variables de entorno relevantes:
- `LW_PROJECT_ROOT`: opcional — fuerza la raíz del proyecto usada por el resolver.
- `LW_CONFIG_DIR`, `LW_SQL_DIR`, `LW_SCRIPTS_DIR`, `LW_TEMPLATES_DIR`, `LW_STATIC_DIR`, `LW_DATA_DIR`: opcionales — sobreescriben las carpetas detectadas para configuración, SQL, scripts, plantillas, estáticos y datos respectivamente.

Notas:
- No se cambió la lógica de negocio; las modificaciones son de estructura/arranque únicamente.
- Si tu CI ejecuta scripts desde un directorio diferente, exporta `LW_PROJECT_ROOT` apuntando al repo raíz.
