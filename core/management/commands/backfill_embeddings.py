"""
Comando de Backfill: Poblar Embeddings para Documentos Existentes
==================================================================

Este comando rellena los embeddings para todos los artículos que actualmente
tienen embedding=NULL en la base de datos.

Características:
- Procesamiento en lotes (batch_size configurable, default: 100)
- Barra de progreso con tqdm
- Manejo robusto de errores (continúa si un documento falla)
- Logging detallado de errores
- Optimización de memoria (no carga todos los documentos a la vez)

Uso:
    python manage.py backfill_embeddings
    python manage.py backfill_embeddings --batch-size 50
    python manage.py backfill_embeddings --limit 1000
    python manage.py backfill_embeddings --force  # Regenerar todos
"""

import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm

from core.models import Article
from services import EmbeddingGenerator

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Rellena embeddings para artículos existentes con embedding=NULL"

    def add_arguments(self, parser):
        """Argumentos del comando"""
        parser.add_argument(
            "--batch-size",
            type=int,
            default=100,
            help="Número de artículos a procesar en cada batch (default: 100)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Límite máximo de artículos a procesar (útil para pruebas)",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Regenerar embeddings para TODOS los artículos (incluso si ya tienen)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simular el proceso sin guardar cambios (modo prueba)",
        )

    def handle(self, *args, **options):
        """Ejecuta el comando de backfill"""
        batch_size = options["batch_size"]
        limit = options["limit"]
        force = options["force"]
        dry_run = options["dry_run"]

        # Banner inicial
        self.stdout.write("=" * 80)
        self.stdout.write(
            self.style.HTTP_INFO("🔄 BACKFILL DE EMBEDDINGS - LegalWatchPR")
        )
        self.stdout.write("=" * 80)

        if dry_run:
            self.stdout.write(
                self.style.WARNING("⚠️  MODO DRY-RUN: No se guardarán cambios")
            )

        # Inicializar generador de embeddings
        try:
            self.stdout.write("🚀 Inicializando modelo de embeddings...")
            generator = EmbeddingGenerator()
            model_info = generator.get_model_info()
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Modelo: {model_info['model_name']} ({model_info['dimension']} dims)"
                )
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error al cargar modelo: {e}"))
            logger.error(f"Error al cargar modelo de embeddings: {e}", exc_info=True)
            return

        # Construir queryset base
        if force:
            queryset = Article.objects.all()
            self.stdout.write(
                self.style.WARNING("⚠️  Modo FORCE: regenerando TODOS los embeddings")
            )
        else:
            queryset = Article.objects.filter(embedding__isnull=True)
            self.stdout.write("📋 Procesando artículos con embedding=NULL")

        # Aplicar límite si se especificó
        total_count = queryset.count()

        if limit:
            self.stdout.write(f"🔒 Limitado a {limit} artículos")
            queryset = queryset[:limit]
            total_count = min(total_count, limit)

        if total_count == 0:
            self.stdout.write(self.style.SUCCESS("✅ No hay artículos para procesar"))
            return

        # Información del proceso
        self.stdout.write(f"\n📊 Total de artículos a procesar: {total_count}")
        self.stdout.write(f"📦 Tamaño de batch: {batch_size}")
        self.stdout.write(
            f"🔢 Número de batches: {(total_count + batch_size - 1) // batch_size}"
        )
        self.stdout.write("-" * 80)

        # Contadores
        processed = 0
        errors = 0
        skipped = 0
        error_details = []

        # Obtener IDs para procesamiento en batches
        article_ids = list(queryset.values_list("id", flat=True))

        # Procesar en batches con barra de progreso
        with tqdm(total=total_count, desc="Procesando artículos", unit="art") as pbar:
            for i in range(0, len(article_ids), batch_size):
                batch_ids = article_ids[i : i + batch_size]
                batch_articles = Article.objects.filter(id__in=batch_ids)

                (i // batch_size) + 1
                (len(article_ids) + batch_size - 1) // batch_size

                # Procesar cada artículo del batch
                for article in batch_articles:
                    try:
                        # Verificar que tenga contenido
                        if not self._has_content(article):
                            skipped += 1
                            pbar.set_postfix(
                                {
                                    "procesados": processed,
                                    "errores": errors,
                                    "omitidos": skipped,
                                }
                            )
                            pbar.update(1)
                            continue

                        # Construir texto para embedding
                        text = self._build_text_for_embedding(article)

                        # Generar embedding
                        embedding = generator.encode(text)

                        # Guardar en base de datos (si no es dry-run)
                        if not dry_run:
                            with transaction.atomic():
                                article.embedding = embedding
                                article.save(update_fields=["embedding"])

                        processed += 1

                        # Actualizar barra de progreso
                        pbar.set_postfix(
                            {
                                "procesados": processed,
                                "errores": errors,
                                "omitidos": skipped,
                            }
                        )
                        pbar.update(1)

                    except Exception as e:
                        # Registrar error y continuar
                        errors += 1
                        error_msg = f"Artículo ID {article.id}: {str(e)[:200]}"
                        error_details.append(error_msg)

                        logger.error(
                            f"Error procesando artículo {article.id}: {e}",
                            exc_info=True,
                        )

                        # Actualizar barra de progreso
                        pbar.set_postfix(
                            {
                                "procesados": processed,
                                "errores": errors,
                                "omitidos": skipped,
                            }
                        )
                        pbar.update(1)

                        # Continuar con el siguiente artículo
                        continue

        # Resumen final
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.HTTP_INFO("📊 RESUMEN DEL BACKFILL"))
        self.stdout.write("=" * 80)

        if dry_run:
            self.stdout.write(
                self.style.WARNING("⚠️  DRY-RUN: Ningún cambio fue guardado")
            )

        self.stdout.write(
            self.style.SUCCESS(f"✅ Procesados exitosamente: {processed}")
        )

        if errors > 0:
            self.stdout.write(self.style.ERROR(f"❌ Errores encontrados: {errors}"))

            # Mostrar primeros 10 errores
            if error_details:
                self.stdout.write("\n🔍 Primeros errores:")
                for error in error_details[:10]:
                    self.stdout.write(f"  • {error}")

                if len(error_details) > 10:
                    self.stdout.write(f"  ... y {len(error_details) - 10} errores más")

        if skipped > 0:
            self.stdout.write(
                self.style.WARNING(f"⚠️  Omitidos (sin contenido): {skipped}")
            )

        # Estadísticas
        self.stdout.write("-" * 80)

        if total_count > 0:
            success_rate = (processed / total_count) * 100
            self.stdout.write(f"📈 Tasa de éxito: {success_rate:.1f}%")

        # Estado final de la base de datos
        if not dry_run:
            remaining = Article.objects.filter(embedding__isnull=True).count()
            total_articles = Article.objects.count()
            populated = total_articles - remaining

            if total_articles > 0:
                coverage = (populated / total_articles) * 100
                self.stdout.write(
                    f"📊 Cobertura de embeddings: {populated}/{total_articles} ({coverage:.1f}%)"
                )

            if remaining == 0:
                self.stdout.write(
                    self.style.SUCCESS("\n🎉 ¡Todos los artículos tienen embeddings!")
                )
            else:
                self.stdout.write(f"📋 Artículos aún sin embedding: {remaining}")

        self.stdout.write("=" * 80)

        # Recomendaciones finales
        if errors > 0:
            self.stdout.write(
                "\n💡 Recomendación: Revisa los logs para más detalles sobre los errores"
            )

        if not dry_run and processed > 0:
            self.stdout.write(
                "\n💡 Siguiente paso: Crear el índice HNSW para búsqueda rápida"
            )
            self.stdout.write(
                "   Comando: python manage.py dbshell < sql/create_hnsw_index.sql"
            )

    def _has_content(self, article):
        """
        Verifica si el artículo tiene contenido suficiente para generar embedding.

        Args:
            article: Instancia de Article

        Returns:
            bool: True si tiene contenido, False en caso contrario
        """
        return bool(
            (article.title and article.title.strip())
            or (article.snippet and article.snippet.strip())
            or (article.ai_summary and article.ai_summary.strip())
        )

    def _build_text_for_embedding(self, article):
        """
        Construye el texto completo para generar el embedding.

        Combina título, snippet y resumen AI con etiquetas descriptivas
        para mejorar la calidad del embedding semántico.

        Args:
            article: Instancia de Article

        Returns:
            str: Texto combinado optimizado para embedding
        """
        parts = []

        # Título (componente principal)
        if article.title and article.title.strip():
            parts.append(f"Título: {article.title.strip()}")

        # Snippet (contenido detallado)
        if article.snippet and article.snippet.strip():
            parts.append(f"Contenido: {article.snippet.strip()}")

        # Resumen AI (contexto adicional)
        if article.ai_summary and article.ai_summary.strip():
            parts.append(f"Resumen: {article.ai_summary.strip()}")

        # Fuente (información de contexto)
        if hasattr(article, "source") and article.source:
            parts.append(f"Fuente: {article.source}")

        # Unir todas las partes
        text = "\n\n".join(parts)

        return text
