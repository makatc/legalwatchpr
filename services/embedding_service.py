"""
Servicio de Generación de Embeddings Semánticos
================================================

Este módulo proporciona un servicio robusto para convertir texto en vectores de embeddings
usando el modelo paraphrase-multilingual-MiniLM-L12-v2 (384 dimensiones).

Características:
- Patrón Singleton para evitar recargar el modelo en cada llamada
- Truncamiento inteligente: conserva inicio + final del documento
- Manejo robusto de excepciones
- Salida compatible con pgvector

Uso:
    from services import EmbeddingGenerator
    
    generator = EmbeddingGenerator()
    embedding = generator.encode("Tu texto aquí")
    # embedding es una lista de 384 floats
"""

import logging
import threading
from typing import List, Optional
from sentence_transformers import SentenceTransformer
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    Generador de embeddings semánticos con patrón Singleton.
    
    Usa el modelo paraphrase-multilingual-MiniLM-L12-v2 que genera vectores de 384 dimensiones
    y soporta múltiples idiomas incluyendo español.
    
    Atributos:
        MODEL_NAME: Nombre del modelo de Hugging Face
        MAX_TOKENS: Límite aproximado de tokens (512 para este modelo)
        DIMENSION: Dimensión de los vectores generados (384)
        _instance: Instancia única del Singleton
        _lock: Lock para thread-safety
        _model: Modelo de SentenceTransformers cargado
    """
    
    MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
    MAX_TOKENS = 512  # Límite de tokens del modelo
    DIMENSION = 384   # Dimensión de los embeddings generados
    
    _instance: Optional['EmbeddingGenerator'] = None
    _lock = threading.Lock()
    _model: Optional[SentenceTransformer] = None
    
    def __new__(cls):
        """
        Implementación del patrón Singleton thread-safe.
        
        Asegura que solo exista una instancia del generador en toda la aplicación,
        evitando recargar el modelo en cada llamada.
        """
        if cls._instance is None:
            with cls._lock:
                # Double-checked locking
                if cls._instance is None:
                    logger.info(f"Inicializando EmbeddingGenerator (Singleton)")
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """
        Inicializa el modelo de embeddings (solo la primera vez).
        """
        if self._initialized:
            return
        
        with self._lock:
            if not self._initialized:
                try:
                    logger.info(f"Cargando modelo: {self.MODEL_NAME}")
                    self._model = SentenceTransformer(self.MODEL_NAME)
                    self._initialized = True
                    logger.info(f"✅ Modelo cargado exitosamente. Dimensión: {self.DIMENSION}")
                except Exception as e:
                    logger.error(f"❌ Error al cargar el modelo: {e}")
                    raise RuntimeError(f"No se pudo cargar el modelo de embeddings: {e}") from e
    
    def _smart_truncate(self, text: str) -> str:
        """
        Truncamiento inteligente: conserva inicio + final del documento.
        
        Estrategia:
        1. Si el texto es corto (< MAX_TOKENS), retornarlo completo
        2. Si es largo, tomar los primeros ~70% de tokens disponibles del inicio
        3. Tomar los últimos ~30% de tokens disponibles del final
        4. Concatenar con " ... " en el medio
        
        Esto captura la introducción (contexto) y la conclusión (decisión/resultado).
        
        Args:
            text: Texto original que puede exceder MAX_TOKENS
            
        Returns:
            Texto truncado inteligentemente
        """
        if not text:
            return ""
        
        # Estimación aproximada: 1 token ≈ 4 caracteres en español
        chars_per_token = 4
        max_chars = self.MAX_TOKENS * chars_per_token
        
        # Si el texto es corto, retornarlo completo
        if len(text) <= max_chars:
            return text
        
        # Calcular cuántos caracteres tomar del inicio y final
        # 70% del inicio, 30% del final
        start_chars = int(max_chars * 0.7)
        end_chars = int(max_chars * 0.3)
        
        # Extraer inicio y final
        start_text = text[:start_chars].rsplit(' ', 1)[0]  # Cortar en palabra completa
        end_text = text[-end_chars:].split(' ', 1)[-1]     # Cortar en palabra completa
        
        # Concatenar con separador
        truncated = f"{start_text} ... {end_text}"
        
        logger.debug(f"Texto truncado: {len(text)} → {len(truncated)} caracteres")
        
        return truncated
    
    def encode(self, text: str, normalize: bool = True) -> List[float]:
        """
        Convierte texto en un vector de embeddings.
        
        Args:
            text: Texto a convertir en embedding
            normalize: Si True, normaliza el vector (recomendado para búsqueda por similitud coseno)
            
        Returns:
            Lista de 384 floats representando el embedding del texto
            
        Raises:
            ValueError: Si el texto está vacío o es None
            RuntimeError: Si ocurre un error durante la generación del embedding
            
        Examples:
            >>> generator = EmbeddingGenerator()
            >>> embedding = generator.encode("Ley de transparencia aprobada")
            >>> len(embedding)
            384
            >>> isinstance(embedding[0], float)
            True
        """
        # Validación de entrada
        if not text or not isinstance(text, str):
            raise ValueError("El texto debe ser una cadena no vacía")
        
        # Limpiar y truncar el texto
        text = text.strip()
        if not text:
            raise ValueError("El texto no puede estar vacío después de limpieza")
        
        text = self._smart_truncate(text)
        
        try:
            # Generar embedding
            logger.debug(f"Generando embedding para texto de {len(text)} caracteres")
            
            # SentenceTransformers retorna numpy array
            embedding_array = self._model.encode(
                text,
                convert_to_numpy=True,
                normalize_embeddings=normalize,
                show_progress_bar=False
            )
            
            # Convertir a lista de floats nativos de Python (compatible con pgvector)
            embedding_list = embedding_array.astype(float).tolist()
            
            # Verificar dimensión
            if len(embedding_list) != self.DIMENSION:
                raise RuntimeError(
                    f"Dimensión incorrecta: esperado {self.DIMENSION}, obtenido {len(embedding_list)}"
                )
            
            logger.debug(f"✅ Embedding generado exitosamente: {self.DIMENSION} dimensiones")
            
            return embedding_list
            
        except Exception as e:
            logger.error(f"❌ Error al generar embedding: {e}")
            raise RuntimeError(f"Error al generar embedding: {e}") from e
    
    def encode_batch(self, texts: List[str], normalize: bool = True) -> List[List[float]]:
        """
        Convierte múltiples textos en embeddings de forma eficiente (batch processing).
        
        Args:
            texts: Lista de textos a convertir
            normalize: Si True, normaliza los vectores
            
        Returns:
            Lista de embeddings (cada uno es una lista de 384 floats)
            
        Raises:
            ValueError: Si texts está vacío o no es una lista
            RuntimeError: Si ocurre un error durante la generación
            
        Examples:
            >>> generator = EmbeddingGenerator()
            >>> texts = ["Ley aprobada", "Sentencia dictada"]
            >>> embeddings = generator.encode_batch(texts)
            >>> len(embeddings)
            2
            >>> len(embeddings[0])
            384
        """
        if not texts or not isinstance(texts, list):
            raise ValueError("texts debe ser una lista no vacía")
        
        # Validar y truncar cada texto
        cleaned_texts = []
        for i, text in enumerate(texts):
            if not text or not isinstance(text, str):
                logger.warning(f"Texto {i} inválido, omitiendo")
                continue
            
            text = text.strip()
            if text:
                cleaned_texts.append(self._smart_truncate(text))
        
        if not cleaned_texts:
            raise ValueError("No hay textos válidos para procesar")
        
        try:
            logger.info(f"Generando embeddings para {len(cleaned_texts)} textos en batch")
            
            # Generar embeddings en batch (más eficiente)
            embeddings_array = self._model.encode(
                cleaned_texts,
                convert_to_numpy=True,
                normalize_embeddings=normalize,
                show_progress_bar=len(cleaned_texts) > 10,  # Mostrar progreso solo si hay muchos
                batch_size=32  # Procesar en lotes de 32
            )
            
            # Convertir a lista de listas de floats
            embeddings_list = [
                row.astype(float).tolist() 
                for row in embeddings_array
            ]
            
            logger.info(f"✅ {len(embeddings_list)} embeddings generados exitosamente")
            
            return embeddings_list
            
        except Exception as e:
            logger.error(f"❌ Error al generar embeddings en batch: {e}")
            raise RuntimeError(f"Error al generar embeddings en batch: {e}") from e
    
    def get_model_info(self) -> dict:
        """
        Retorna información sobre el modelo cargado.
        
        Returns:
            Diccionario con información del modelo
        """
        return {
            'model_name': self.MODEL_NAME,
            'max_tokens': self.MAX_TOKENS,
            'dimension': self.DIMENSION,
            'initialized': self._initialized,
            'max_seq_length': self._model.max_seq_length if self._model else None,
        }


# Función auxiliar para uso directo
def generate_embedding(text: str) -> List[float]:
    """
    Función auxiliar para generar un embedding de forma directa.
    
    Args:
        text: Texto a convertir en embedding
        
    Returns:
        Lista de 384 floats
        
    Examples:
        >>> from services.embedding_service import generate_embedding
        >>> embedding = generate_embedding("Ejemplo de texto")
        >>> len(embedding)
        384
    """
    generator = EmbeddingGenerator()
    return generator.encode(text)
