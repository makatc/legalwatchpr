"""
Señales para generación automática de embeddings
=================================================

Este módulo registra señales Django para automatizar la generación
de embeddings semánticos cuando se crean o actualizan artículos.
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import Article
from services.embedding_service import EmbeddingGenerator

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Article)
def auto_generate_embedding(sender, instance, created, **kwargs):
    """
    Genera automáticamente embedding para artículos nuevos o sin embedding.
    
    Args:
        sender: Clase del modelo (Article)
        instance: Instancia del artículo guardado
        created: True si es un nuevo objeto, False si es actualización
        **kwargs: Argumentos adicionales de la señal
    
    Nota:
        Usa update_fields=['embedding'] para evitar bucles infinitos de señales.
    """
    # Solo generar si es nuevo O si no tiene embedding
    if not created and instance.embedding is not None:
        return
    
    try:
        # Concatenar título y snippet para generar embedding
        text = f"{instance.title} {instance.snippet or ''}".strip()
        
        if not text:
            logger.warning(f"Article {instance.id} tiene título y snippet vacíos, saltando embedding")
            return
        
        # Instanciar generador y crear embedding
        generator = EmbeddingGenerator()
        embedding = generator.encode(text, normalize=True)
        
        if embedding is None:
            logger.warning(f"No se pudo generar embedding para Article {instance.id}")
            return
        
        # Guardar usando update_fields para prevenir recursión
        instance.embedding = embedding
        instance.save(update_fields=['embedding'])
        
        logger.info(f"✅ Embedding generado automáticamente para Article {instance.id}")
    
    except Exception as e:
        # NO propagamos el error para evitar que falle el guardado del artículo
        logger.error(f"Error generando embedding para Article {instance.id}: {e}", exc_info=True)
