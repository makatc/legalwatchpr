-- ============================================================================
-- CREAR ÍNDICE HNSW PARA BÚSQUEDA SEMÁNTICA (SIN DOWNTIME)
-- ============================================================================
-- Este script crea el índice HNSW para el campo embedding de forma segura.
-- EJECUTAR DESPUÉS de aplicar la migración 0020_add_hybrid_search_fields.py
--
-- PARÁMETROS DEL ÍNDICE:
-- - m=16: Número de conexiones bidireccionales por capa (tradeoff: precisión vs tamaño)
-- - ef_construction=64: Tamaño de la lista dinámica durante construcción (mayor = más preciso pero más lento)
-- - opclasses=['vector_cosine_ops']: Operador de distancia coseno (ideal para embeddings normalizados)
--
-- NOTA IMPORTANTE: pgvector NO soporta CREATE INDEX CONCURRENTLY para HNSW
-- Por lo tanto, este índice SE BLOQUEARÁ la tabla durante su creación.
-- Ejecutar en horario de bajo tráfico o durante ventana de mantenimiento.
-- ============================================================================

-- PASO 1: Verificar que pgvector está instalado
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        RAISE EXCEPTION 'La extensión pgvector no está instalada. Ejecuta: CREATE EXTENSION vector;';
    END IF;
END $$;

-- PASO 2: Verificar que el campo embedding existe
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'core_article' AND column_name = 'embedding'
    ) THEN
        RAISE EXCEPTION 'El campo embedding no existe. Ejecuta primero la migración 0020.';
    END IF;
END $$;

-- PASO 3: Crear índice HNSW (BLOQUEA LA TABLA - cuidado en producción)
CREATE INDEX IF NOT EXISTS idx_article_embedding_hnsw 
ON core_article 
USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 64);

-- PASO 4: Verificar que el índice fue creado
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE indexname = 'idx_article_embedding_hnsw';

-- PASO 5: Estadísticas del índice (opcional)
SELECT 
    pg_size_pretty(pg_relation_size('idx_article_embedding_hnsw')) AS index_size,
    (SELECT COUNT(*) FROM core_article WHERE embedding IS NOT NULL) AS indexed_rows;

-- ============================================================================
-- ALTERNATIVA PARA MINIMIZAR DOWNTIME (si hay muchos registros):
-- ============================================================================
-- 1. Crear una tabla temporal con solo los artículos que tienen embeddings
-- 2. Crear el índice en la tabla temporal
-- 3. Hacer SWAP de tablas atómicamente
-- 
-- Ejemplo (AVANZADO - solo si tienes > 100k registros):
-- 
-- CREATE TABLE core_article_new (LIKE core_article INCLUDING ALL);
-- INSERT INTO core_article_new SELECT * FROM core_article;
-- CREATE INDEX idx_article_embedding_hnsw ON core_article_new USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
-- BEGIN;
-- ALTER TABLE core_article RENAME TO core_article_old;
-- ALTER TABLE core_article_new RENAME TO core_article;
-- COMMIT;
-- DROP TABLE core_article_old;
-- ============================================================================

-- ROLLBACK (para deshacer si algo falla):
-- DROP INDEX IF EXISTS idx_article_embedding_hnsw;
