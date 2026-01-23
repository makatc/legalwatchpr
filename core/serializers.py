"""
Serializadores para la API de Búsqueda
======================================

Serializadores de Django REST Framework para la API de búsqueda híbrida.
"""

from rest_framework import serializers

from core.models import Article


class ArticleSearchResultSerializer(serializers.Serializer):
    """
    Serializer para resultados de búsqueda híbrida.
    
    Incluye información del artículo y métricas de relevancia.
    """
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True)
    snippet = serializers.CharField(read_only=True, allow_null=True)
    link = serializers.URLField(read_only=True, source='url', allow_null=True)  # Mapear 'url' del SQL a 'link' del modelo
    published_at = serializers.DateTimeField(read_only=True, source='published_date', allow_null=True)  # Mapear published_date
    source = serializers.CharField(read_only=True, allow_null=True)
    ai_summary = serializers.CharField(read_only=True, allow_null=True)
    
    # Métricas de relevancia
    rrf_score = serializers.FloatField(read_only=True)
    semantic_rank = serializers.IntegerField(read_only=True, allow_null=True)
    keyword_rank = serializers.IntegerField(read_only=True, allow_null=True)
    
    class Meta:
        fields = [
            'id', 'title', 'snippet', 'link', 'published_at', 'source', 
            'ai_summary', 'rrf_score', 'semantic_rank', 'keyword_rank'
        ]


class ArticleSerializer(serializers.ModelSerializer):
    """
    Serializer estándar para el modelo Article.
    """
    class Meta:
        model = Article
        fields = [
            'id', 'title', 'snippet', 'link', 'published_at', 
            'source', 'ai_summary', 'created_at'
        ]
        read_only_fields = fields


class SearchStatsSerializer(serializers.Serializer):
    """
    Serializer para estadísticas de búsqueda.
    """
    total_articles = serializers.IntegerField(read_only=True)
    articles_with_embedding = serializers.IntegerField(read_only=True)
    articles_with_search_vector = serializers.IntegerField(read_only=True)
    articles_searchable = serializers.IntegerField(read_only=True)
    embedding_coverage = serializers.FloatField(read_only=True)
    search_vector_coverage = serializers.FloatField(read_only=True)
