"""
Comando de Django: Generar Embeddings para Artículos
=====================================================

Este comando genera embeddings semánticos para todos los artículos de LegalWatchPR
que aún no tienen embeddings o para todos si se especifica --force.

Uso:
    python manage.py generate_embeddings
    python manage.py generate_embeddings --force  # Regenerar todos
    python manage.py generate_embeddings --batch-size 50
    python manage.py generate_embeddings --limit 100  # Procesar solo 100
"""

import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Article
from services import EmbeddingGenerator

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Genera embeddings semánticos para artículos sin embeddings'
    
    def add_arguments(self, parser):
        """Argumentos del comando"""
        parser.add_argument(
            '--force',
            action='store_true',
            help='Regenerar embeddings para TODOS los artículos (incluso si ya tienen)',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=32,
            help='Número de artículos a procesar en cada batch (default: 32)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Límite de artículos a procesar (útil para pruebas)',
        )
        parser.add_argument(
            '--article-id',
            type=int,
            default=None,
            help='Procesar solo un artículo específico por ID',
        )
    
    def handle(self, *args, **options):
        """Ejecuta el comando"""
        force = options['force']
        batch_size = options['batch_size']
        limit = options['limit']
        article_id = options['article_id']
        
        self.stdout.write(self.style.HTTP_INFO('=' * 70))
        self.stdout.write(self.style.HTTP_INFO('🚀 Generador de Embeddings - LegalWatchPR'))
        self.stdout.write(self.style.HTTP_INFO('=' * 70))
        
        # Inicializar el generador de embeddings
        try:
            self.stdout.write('Inicializando modelo de embeddings...')
            generator = EmbeddingGenerator()
            model_info = generator.get_model_info()
            self.stdout.write(self.style.SUCCESS(
                f"✅ Modelo cargado: {model_info['model_name']} "
                f"({model_info['dimension']} dimensiones)"
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error al cargar el modelo: {e}"))
            return
        
        # Construir queryset
        if article_id:
            # Procesar solo un artículo específico
            queryset = Article.objects.filter(id=article_id)
            if not queryset.exists():
                self.stdout.write(self.style.ERROR(f"❌ No existe artículo con ID {article_id}"))
                return
            self.stdout.write(f"Procesando artículo ID: {article_id}")
        elif force:
            # Procesar todos los artículos
            queryset = Article.objects.all()
            self.stdout.write(self.style.WARNING('⚠️  Modo FORCE: regenerando TODOS los embeddings'))
        else:
            # Procesar solo artículos sin embedding
            queryset = Article.objects.filter(embedding__isnull=True)
            self.stdout.write('Procesando solo artículos SIN embeddings')
        
        # Aplicar límite si se especificó
        if limit:
            queryset = queryset[:limit]
            self.stdout.write(f"Limitado a {limit} artículos")
        
        # Contar total
        total_count = queryset.count()
        
        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('✅ No hay artículos para procesar'))
            return
        
        self.stdout.write(f"\n📊 Total de artículos a procesar: {total_count}")
        self.stdout.write(f"📦 Tamaño de batch: {batch_size}")
        self.stdout.write('-' * 70)
        
        # Procesamiento en batches
        processed = 0
        errors = 0
        skipped = 0
        
        # Obtener IDs para procesar en batches
        article_ids = list(queryset.values_list('id', flat=True))
        
        for i in range(0, len(article_ids), batch_size):
            batch_ids = article_ids[i:i + batch_size]
            batch_articles = Article.objects.filter(id__in=batch_ids)
            
            batch_num = (i // batch_size) + 1
            total_batches = (len(article_ids) + batch_size - 1) // batch_size
            
            self.stdout.write(f"\n🔄 Procesando batch {batch_num}/{total_batches} ({len(batch_ids)} artículos)...")
            
            # Procesar cada artículo del batch
            for article in batch_articles:
                try:
                    # Verificar que tenga contenido para generar embedding
                    if not self._has_content(article):
                        self.stdout.write(
                            self.style.WARNING(f"  ⚠️  Artículo {article.id}: sin contenido, omitiendo")
                        )
                        skipped += 1
                        continue
                    
                    # Crear texto completo para embedding
                    text = self._build_text_for_embedding(article)
                    
                    # Generar embedding
                    embedding = generator.encode(text)
                    
                    # Guardar en la base de datos
                    with transaction.atomic():
                        article.embedding = embedding
                        article.save(update_fields=['embedding'])
                    
                    processed += 1
                    
                    # Mostrar progreso cada 10 artículos
                    if processed % 10 == 0:
                        progress_pct = (processed / total_count) * 100
                        self.stdout.write(
                            f"  📈 Progreso: {processed}/{total_count} ({progress_pct:.1f}%)"
                        )
                    
                except Exception as e:
                    errors += 1
                    logger.error(f"Error procesando artículo {article.id}: {e}")
                    self.stdout.write(
                        self.style.ERROR(f"  ❌ Artículo {article.id}: {str(e)[:100]}")
                    )
                    continue
        
        # Resumen final
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.HTTP_INFO('📊 RESUMEN FINAL'))
        self.stdout.write('=' * 70)
        self.stdout.write(self.style.SUCCESS(f"✅ Procesados exitosamente: {processed}"))
        
        if errors > 0:
            self.stdout.write(self.style.ERROR(f"❌ Errores: {errors}"))
        
        if skipped > 0:
            self.stdout.write(self.style.WARNING(f"⚠️  Omitidos (sin contenido): {skipped}"))
        
        self.stdout.write('-' * 70)
        
        # Calcular tasa de éxito
        if total_count > 0:
            success_rate = (processed / total_count) * 100
            self.stdout.write(f"Tasa de éxito: {success_rate:.1f}%")
        
        # Verificar estado final
        remaining = Article.objects.filter(embedding__isnull=True).count()
        self.stdout.write(f"Artículos aún sin embedding: {remaining}")
        
        if remaining == 0:
            self.stdout.write(self.style.SUCCESS('\n🎉 ¡Todos los artículos tienen embeddings!'))
        
        self.stdout.write('\n' + '=' * 70)
    
    def _has_content(self, article):
        """
        Verifica si el artículo tiene contenido suficiente para generar embedding.
        
        Args:
            article: Instancia de Article
            
        Returns:
            bool: True si tiene contenido, False en caso contrario
        """
        # Debe tener al menos título o snippet o ai_summary
        return bool(
            (article.title and article.title.strip()) or
            (article.snippet and article.snippet.strip()) or
            (article.ai_summary and article.ai_summary.strip())
        )
    
    def _build_text_for_embedding(self, article):
        """
        Construye el texto completo para generar el embedding.
        
        Combina título, snippet y resumen AI para capturar el contenido completo
        del artículo en el embedding.
        
        Args:
            article: Instancia de Article
            
        Returns:
            str: Texto combinado para embedding
        """
        parts = []
        
        # Título (peso más alto en el embedding)
        if article.title and article.title.strip():
            parts.append(f"Título: {article.title.strip()}")
        
        # Snippet (contenido principal)
        if article.snippet and article.snippet.strip():
            parts.append(f"Contenido: {article.snippet.strip()}")
        
        # Resumen AI (información adicional)
        if article.ai_summary and article.ai_summary.strip():
            parts.append(f"Resumen: {article.ai_summary.strip()}")
        
        # Unir todas las partes con saltos de línea
        text = '\n\n'.join(parts)
        
        return text
