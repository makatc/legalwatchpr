# Aplicación de Índices Sin Downtime - Guía de Producción

## 🎯 Objetivo
Aplicar la migración `0020_add_hybrid_search_fields` y crear índices de búsqueda híbrida **sin bloquear la base de datos** en producción.

---

## 📋 Orden de Operaciones

### **PASO 1: Aplicar Migración (SEGURO - No bloquea)**

La migración añade dos campos NULL, lo cual **NO requiere reescribir la tabla** y por lo tanto es instantáneo:

```bash
python manage.py migrate core 0020
```

**¿Qué hace?**
- ✅ Añade campo `search_vector` (SearchVectorField, NULL permitido)
- ✅ Añade campo `embedding` (VectorField 384 dims, NULL permitido)
- ✅ Crea índice GIN con `CREATE INDEX CONCURRENTLY` (no bloquea)

**Tiempo estimado:** 1-5 segundos (independiente del número de registros)

---

### **PASO 2: Verificar Estado**

```bash
python check_indexes.py
```

Deberías ver:
```
✅ search_vector     | Tipo: tsvector  | NULL: YES
✅ embedding         | Tipo: vector    | NULL: YES
✅ idx_article_search_vector (GIN)
```

---

### **PASO 3: Poblar search_vector (Opcional pero Recomendado)**

Antes de crear el índice HNSW, es útil poblar los `search_vector` para búsqueda léxica:

```bash
python manage.py shell < populate_search_vectors.py
```

Este script actualiza los artículos en **lotes de 1000** sin bloquear:

```python
from django.contrib.postgres.search import SearchVector
from core.models import Article

# Actualizar en lotes
batch_size = 1000
updated = 0

while True:
    articles = Article.objects.filter(search_vector__isnull=True)[:batch_size]
    if not articles:
        break
    
    for article in articles:
        article.search_vector = SearchVector('title', weight='A') + SearchVector('snippet', weight='B')
        article.save(update_fields=['search_vector'])
    
    updated += len(articles)
    print(f"Actualizados: {updated}")
```

**Tiempo estimado:** 10-30 segundos por cada 10,000 artículos

---

### **PASO 4: Crear Índice HNSW (CUIDADO - Bloquea Tabla)**

⚠️ **IMPORTANTE:** La creación del índice HNSW **BLOQUEA ESCRITURAS** en la tabla.

#### **Opción A: Ejecución Directa (Bases de Datos Pequeñas < 100k registros)**

Si tienes menos de 100,000 artículos y puedes permitir 1-5 minutos de bloqueo:

```bash
# Desde psql
psql -U tu_usuario -d legalwatchpr -f sql/create_hnsw_index.sql

# O desde Django shell
python manage.py dbshell < sql/create_hnsw_index.sql
```

**Tiempo estimado:**
- 10,000 artículos: ~30 segundos
- 50,000 artículos: ~2 minutos
- 100,000 artículos: ~5 minutos

#### **Opción B: Ventana de Mantenimiento (Recomendado para Producción)**

1. **Programar en horario de bajo tráfico** (3-5 AM)
2. **Notificar a usuarios** del mantenimiento
3. **Ejecutar script** con monitoreo

```bash
# Iniciar monitoreo en terminal separada
watch -n 1 'psql -U tu_usuario -d legalwatchpr -c "SELECT * FROM pg_stat_progress_create_index;"'

# Ejecutar creación de índice
psql -U tu_usuario -d legalwatchpr -f sql/create_hnsw_index.sql
```

#### **Opción C: Blue-Green Deployment (Sin Downtime - Avanzado)**

Para bases de datos grandes (> 100k registros) donde no puedes permitir downtime:

1. **Crear réplica temporal de la tabla:**
   ```sql
   CREATE TABLE core_article_new (LIKE core_article INCLUDING ALL);
   INSERT INTO core_article_new SELECT * FROM core_article;
   ```

2. **Crear índice en la réplica:**
   ```sql
   CREATE INDEX idx_article_embedding_hnsw 
   ON core_article_new 
   USING hnsw (embedding vector_cosine_ops) 
   WITH (m = 16, ef_construction = 64);
   ```

3. **Swap atómico de tablas:**
   ```sql
   BEGIN;
   ALTER TABLE core_article RENAME TO core_article_old;
   ALTER TABLE core_article_new RENAME TO core_article;
   COMMIT;
   ```

4. **Sincronizar datos que cambiaron durante la construcción:**
   ```sql
   INSERT INTO core_article 
   SELECT * FROM core_article_old 
   WHERE id NOT IN (SELECT id FROM core_article);
   ```

5. **Eliminar tabla antigua:**
   ```sql
   DROP TABLE core_article_old;
   ```

**Tiempo estimado total:** 10-20 minutos, pero **sin downtime perceptible**

---

### **PASO 5: Verificar Índice HNSW Creado**

```bash
python check_indexes.py
```

Deberías ver:
```
✅ idx_article_embedding_hnsw
   Tamaño: 45 MB
   Definición: CREATE INDEX idx_article_embedding_hnsw ON core_article USING hnsw (embedding vector_cosine_ops)...
```

---

## 📊 Monitoreo Durante la Creación

### Verificar progreso del índice:

```sql
SELECT 
    phase,
    blocks_done,
    blocks_total,
    ROUND(100.0 * blocks_done / NULLIF(blocks_total, 0), 2) AS percent_done
FROM pg_stat_progress_create_index;
```

### Ver locks activos:

```sql
SELECT 
    pid,
    usename,
    state,
    query,
    age(clock_timestamp(), query_start) AS duration
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY duration DESC;
```

### Cancelar creación de índice (si es necesario):

```sql
-- Encontrar PID del proceso
SELECT pid FROM pg_stat_progress_create_index;

-- Cancelar (el índice se eliminará automáticamente)
SELECT pg_cancel_backend(PID_AQUI);
```

---

## ⚡ Resumen de Tiempos de Bloqueo

| Operación | Bloquea Escrituras | Bloquea Lecturas | Tiempo (10k rows) | Tiempo (100k rows) |
|-----------|-------------------|------------------|-------------------|---------------------|
| `migrate 0020` | ❌ No | ❌ No | < 1 segundo | < 1 segundo |
| Poblar `search_vector` | ✅ Sí (por lote) | ❌ No | ~10 segundos | ~100 segundos |
| Crear índice GIN | ❌ No (CONCURRENT) | ❌ No | ~5 segundos | ~30 segundos |
| Crear índice HNSW | ✅ **SÍ** | ❌ No | ~30 segundos | ~5 minutos |

---

## 🔧 Rollback (Si algo falla)

### Revertir migración:
```bash
python manage.py migrate core 0019
```

### Eliminar índices manualmente:
```sql
DROP INDEX IF EXISTS idx_article_search_vector;
DROP INDEX IF EXISTS idx_article_embedding_hnsw;
```

### Eliminar campos:
```sql
ALTER TABLE core_article DROP COLUMN search_vector;
ALTER TABLE core_article DROP COLUMN embedding;
```

---

## ✅ Checklist de Producción

Antes de ejecutar en producción, verifica:

- [ ] Backup de base de datos creado
- [ ] Extensión pgvector instalada (`CREATE EXTENSION vector;`)
- [ ] Ventana de mantenimiento programada (si aplica)
- [ ] Notificación a usuarios enviada
- [ ] Monitoreo de performance activo
- [ ] Plan de rollback documentado
- [ ] Script de verificación ejecutado en staging primero

---

## 📞 Contacto en Caso de Problemas

Si durante la migración encuentras:
- **Bloqueos prolongados:** Revisar `pg_stat_activity`
- **Errores de memoria:** Incrementar `maintenance_work_mem` temporalmente
- **Índice corrupto:** Eliminar y recrear con `REINDEX`

Logs relevantes:
```bash
# Ver últimas entradas del log de PostgreSQL
tail -f /var/log/postgresql/postgresql-15-main.log
```
