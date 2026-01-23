"""
Servicio de Búsqueda Híbrida con Reciprocal Rank Fusion (RRF)
==============================================================

Este módulo implementa búsqueda híbrida combinando:
1. Búsqueda semántica (embeddings con pgvector)
2. Búsqueda léxica (full-text search con tsvector)

Usa el algoritmo RRF (Reciprocal Rank Fusion) para fusionar y rankear
los resultados de ambas estrategias.

Fórmula RRF:
    rrf_score = 1/(k + rank_semantic) + 1/(k + rank_lexical)
    donde k = 60 (constante estándar)

Referencias:
    - RRF Paper: https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf
"""

import logging
from typing import List, Dict, Any, Optional
from django.db import connection
from services import EmbeddingGenerator

logger = logging.getLogger(__name__)


# Constante RRF estándar
RRF_K = 60


def search_documents(
    query: str,
    limit: int = 20,
    k: int = RRF_K,
    top_k_candidates: int = 100
) -> List[Dict[str, Any]]:
    """
    Búsqueda híbrida de documentos usando RRF (Reciprocal Rank Fusion).
    
    Combina búsqueda semántica (embeddings) y búsqueda léxica (full-text)
    para obtener resultados más relevantes y robustos.
    
    Args:
        query: Texto de búsqueda del usuario
        limit: Número máximo de resultados a retornar (default: 20)
        k: Constante RRF para suavizar rankings (default: 60)
        top_k_candidates: Número de candidatos a considerar de cada método (default: 100)
        
    Returns:
        Lista de diccionarios con información de artículos ordenados por relevancia:
        [
            {
                'id': int,
                'title': str,
                'snippet': str,
                'url': str,
                'published_date': datetime,
                'rrf_score': float,
                'semantic_rank': int or None,
                'keyword_rank': int or None
            },
            ...
        ]
        
    Raises:
        ValueError: Si la query está vacía
        RuntimeError: Si ocurre un error durante la búsqueda
        
    Examples:
        >>> results = search_documents("ley de transparencia")
        >>> len(results) <= 20
        True
        >>> results[0]['rrf_score'] >= results[1]['rrf_score']
        True
    """
    # Validación de entrada
    if not query or not isinstance(query, str):
        raise ValueError("La query debe ser una cadena no vacía")
    
    query = query.strip()
    if not query:
        raise ValueError("La query no puede estar vacía")
    
    logger.info(f"Búsqueda híbrida: '{query}' (limit={limit}, k={k})")
    
    try:
        # Generar embedding para la query
        generator = EmbeddingGenerator()
        query_embedding = generator.encode(query)
        
        # Construir la consulta SQL con CTEs
        sql = """
        WITH semantic AS (
            -- CTE 1: Búsqueda semántica por similitud de embeddings
            -- Usa operador <=> para distancia coseno (pgvector)
            -- Retorna top 100 vecinos más cercanos con su ranking
            SELECT 
                id,
                RANK() OVER (ORDER BY embedding <=> %s::vector) AS rank
            FROM core_article
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        ),
        keyword AS (
            -- CTE 2: Búsqueda léxica full-text con PostgreSQL
            -- Usa ts_rank_cd para ranking de relevancia con densidad de cobertura
            -- websearch_to_tsquery permite sintaxis tipo Google ("frase exacta", OR, -)
            SELECT 
                id,
                RANK() OVER (
                    ORDER BY ts_rank_cd(
                        search_vector, 
                        websearch_to_tsquery('spanish', %s)
                    ) DESC
                ) AS rank
            FROM core_article
            WHERE search_vector @@ websearch_to_tsquery('spanish', %s)
            LIMIT %s
        )
        -- Query principal: FULL OUTER JOIN para combinar ambos resultados
        -- Algunos artículos pueden aparecer solo en semántica, solo en léxica, o en ambas
        SELECT 
            COALESCE(semantic.id, keyword.id) AS id,
            
            -- Calcular RRF score: suma de contribuciones de ambos métodos
            -- COALESCE maneja NULLs cuando un artículo aparece solo en un método
            COALESCE(1.0 / (%s + semantic.rank), 0.0) + 
            COALESCE(1.0 / (%s + keyword.rank), 0.0) AS rrf_score,
            
            -- Mantener rankings individuales para debugging/análisis
            semantic.rank AS semantic_rank,
            keyword.rank AS keyword_rank,
            
            -- Información del artículo
            a.title,
            a.snippet,
            a.link,
            a.published_at,
            ns.name AS source,
            a.ai_summary
            
        FROM semantic
        FULL OUTER JOIN keyword ON semantic.id = keyword.id
        LEFT JOIN core_article a ON COALESCE(semantic.id, keyword.id) = a.id
        LEFT JOIN core_newssource ns ON a.source_id = ns.id
        
        -- Ordenar por RRF score descendente (mejor score primero)
        ORDER BY rrf_score DESC
        
        -- Limitar resultados finales
        LIMIT %s;
        """
        
        # Parámetros de la consulta
        # Nota: query_embedding se pasa dos veces para el CTE semantic
        params = [
            query_embedding,  # semantic CTE: embedding <=> %s
            query_embedding,  # semantic CTE: ORDER BY
            top_k_candidates,  # semantic CTE: LIMIT
            query,             # keyword CTE: websearch_to_tsquery
            query,             # keyword CTE: WHERE clause
            top_k_candidates,  # keyword CTE: LIMIT
            k,                 # RRF constant (semantic)
            k,                 # RRF constant (keyword)
            limit              # Final LIMIT
        ]
        
        # Ejecutar consulta
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
        
        # Convertir resultados a lista de diccionarios
        results = []
        for row in rows:
            result = dict(zip(columns, row))
            # Mapear nombres de campos SQL a nombres esperados por el serializer
            if 'link' in result:
                result['url'] = result['link']  # link del modelo -> url para compatibilidad
            if 'published_at' in result:
                result['published_date'] = result['published_at']  # published_at -> published_date
            results.append(result)
        
        logger.info(f"✅ Búsqueda completada: {len(results)} resultados encontrados")
        
        # Log de estadísticas
        if results:
            semantic_only = sum(1 for r in results if r['semantic_rank'] and not r['keyword_rank'])
            keyword_only = sum(1 for r in results if r['keyword_rank'] and not r['semantic_rank'])
            both = sum(1 for r in results if r['semantic_rank'] and r['keyword_rank'])
            
            logger.debug(f"Distribución: {semantic_only} solo semántica, "
                        f"{keyword_only} solo léxica, {both} en ambas")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Error en búsqueda híbrida: {e}", exc_info=True)
        raise RuntimeError(f"Error durante la búsqueda: {e}") from e


def search_semantic_only(
    query: str,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Búsqueda semántica pura (solo embeddings, sin full-text).
    
    Útil para comparar rendimiento o cuando se desea solo similitud semántica.
    
    Args:
        query: Texto de búsqueda
        limit: Número de resultados
        
    Returns:
        Lista de artículos ordenados por similitud semántica
    """
    if not query or not isinstance(query, str):
        raise ValueError("La query debe ser una cadena no vacía")
    
    query = query.strip()
    if not query:
        raise ValueError("La query no puede estar vacía")
    
    logger.info(f"Búsqueda semántica pura: '{query}' (limit={limit})")
    
    try:
        # Generar embedding
        generator = EmbeddingGenerator()
        query_embedding = generator.encode(query)
        
        # Consulta semántica simple
        sql = """
        SELECT 
            a.id,
            a.title,
            a.snippet,
            a.link,
            a.published_at,
            ns.name AS source,
            a.ai_summary,
            a.embedding <=> %s::vector AS distance,
            1 - (a.embedding <=> %s::vector) AS similarity
        FROM core_article a
        LEFT JOIN core_newssource ns ON a.source_id = ns.id
        WHERE a.embedding IS NOT NULL
        ORDER BY a.embedding <=> %s::vector
        LIMIT %s;
        """
        
        params = [query_embedding, query_embedding, query_embedding, limit]
        
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
        
        results = [dict(zip(columns, row)) for row in rows]
        
        logger.info(f"✅ Búsqueda semántica: {len(results)} resultados")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Error en búsqueda semántica: {e}", exc_info=True)
        raise RuntimeError(f"Error durante búsqueda semántica: {e}") from e


def search_keyword_only(
    query: str,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Búsqueda léxica pura (solo full-text, sin embeddings).
    
    Útil para comparar rendimiento o cuando se desea solo coincidencia textual.
    
    Args:
        query: Texto de búsqueda
        limit: Número de resultados
        
    Returns:
        Lista de artículos ordenados por relevancia léxica
    """
    if not query or not isinstance(query, str):
        raise ValueError("La query debe ser una cadena no vacía")
    
    query = query.strip()
    if not query:
        raise ValueError("La query no puede estar vacía")
    
    logger.info(f"Búsqueda léxica pura: '{query}' (limit={limit})")
    
    try:
        # Consulta full-text simple
        sql = """
        SELECT 
            a.id,
            a.title,
            a.snippet,
            a.link,
            a.published_at,
            ns.name AS source,
            a.ai_summary,
            ts_rank_cd(a.search_vector, websearch_to_tsquery('spanish', %s)) AS rank_score
        FROM core_article a
        LEFT JOIN core_newssource ns ON a.source_id = ns.id
        WHERE a.search_vector @@ websearch_to_tsquery('spanish', %s)
        ORDER BY ts_rank_cd(a.search_vector, websearch_to_tsquery('spanish', %s)) DESC
        LIMIT %s;
        """
        
        params = [query, query, query, limit]
        
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
        
        results = [dict(zip(columns, row)) for row in rows]
        
        logger.info(f"✅ Búsqueda léxica: {len(results)} resultados")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Error en búsqueda léxica: {e}", exc_info=True)
        raise RuntimeError(f"Error durante búsqueda léxica: {e}") from e


def get_search_stats() -> Dict[str, Any]:
    """
    Obtiene estadísticas sobre el estado de búsqueda en la base de datos.
    
    Returns:
        Diccionario con estadísticas:
        {
            'total_articles': int,
            'articles_with_embedding': int,
            'articles_with_search_vector': int,
            'articles_searchable': int,  # Tienen ambos campos
            'embedding_coverage': float,  # Porcentaje
            'search_vector_coverage': float  # Porcentaje
        }
    """
    sql = """
    SELECT 
        COUNT(*) AS total,
        COUNT(embedding) AS with_embedding,
        COUNT(search_vector) AS with_search_vector,
        COUNT(*) FILTER (WHERE embedding IS NOT NULL AND search_vector IS NOT NULL) AS searchable
    FROM core_article;
    """
    
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            row = cursor.fetchone()
        
        total, with_embedding, with_search_vector, searchable = row
        
        stats = {
            'total_articles': total,
            'articles_with_embedding': with_embedding,
            'articles_with_search_vector': with_search_vector,
            'articles_searchable': searchable,
            'embedding_coverage': (with_embedding / total * 100) if total > 0 else 0.0,
            'search_vector_coverage': (with_search_vector / total * 100) if total > 0 else 0.0,
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}", exc_info=True)
        raise
