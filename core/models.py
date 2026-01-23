from django.db import models
from django.utils import timezone
from datetime import time
import os
from pypdf import PdfReader
import docx  # LIBRERÍA NUEVA PARA WORD
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex
from pgvector.django import VectorField, HnswIndex

# --- 1. GESTIÓN DE NOTICIAS ---
class NewsSource(models.Model):
    name = models.CharField(max_length=100)
    url = models.URLField()
    icon_class = models.CharField(max_length=50, default="fas fa-newspaper")
    is_active = models.BooleanField(default=True)

    def __str__(self): return self.name

class Article(models.Model):
    source = models.ForeignKey(NewsSource, on_delete=models.CASCADE)
    title = models.CharField(max_length=500)
    link = models.URLField(max_length=500, unique=True)
    published_at = models.DateTimeField()
    snippet = models.TextField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    ai_summary = models.TextField(blank=True, null=True)
    content_hash = models.CharField(max_length=32, blank=True, null=True, help_text="Hash MD5 del contenido")
    relevance_score = models.FloatField(
        default=0.0,
        help_text="Score de relevancia calculado (0-100)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    # CAMPO PARA BÚSQUEDA FULL-TEXT (PostgreSQL tsvector)
    search_vector = SearchVectorField(
        null=True, 
        blank=True,
        help_text="Vector de búsqueda full-text precomputado (PostgreSQL tsvector)"
    )
    
    # CAMPO PARA EMBEDDINGS SEMÁNTICOS (pgvector - 384 dimensiones)
    embedding = VectorField(
        dimensions=384,  # paraphrase-multilingual-MiniLM-L12-v2
        null=True,
        blank=True,
        help_text="Vector de embeddings semánticos (384 dimensiones)"
    )
    
    class Meta:
        ordering = ['-published_at']
        indexes = [
            # Índice GIN para búsqueda full-text léxica
            GinIndex(fields=['search_vector'], name='idx_article_search_vector'),
            # NOTA: Índice HNSW para embeddings se crea manualmente (ver create_hnsw_index.sql)
        ]
    
    def save(self, *args, **kwargs):
        # Calcular hash del contenido si existe snippet
        if self.snippet:
            import hashlib
            self.content_hash = hashlib.md5(self.snippet.encode('utf-8')).hexdigest()
        super().save(*args, **kwargs)

    def __str__(self): return self.title


class NewsPreset(models.Model):
    SEARCH_METHOD_CHOICES = [
        ('hybrid', 'Búsqueda Híbrida (RRF)'),
        ('semantic', 'Búsqueda Semántica (IA)'),
        ('keyword', 'Búsqueda por Palabras Clave'),
    ]
    
    name = models.CharField(max_length=100)
    keywords = models.TextField(help_text="Separadas por coma")
    threshold = models.IntegerField(
        default=15,
        help_text="Score mínimo de relevancia (0-100) para incluir artículo. Recomendado: 15-20 para alta sensibilidad"
    )
    fields_to_analyze = models.CharField(
        max_length=100,
        default="title,description",
        help_text="Campos a analizar separados por coma: title, description"
    )
    search_method = models.CharField(
        max_length=20,
        choices=SEARCH_METHOD_CHOICES,
        default='hybrid',
        help_text="Método de búsqueda: híbrida (RRF), semántica (IA) o por palabras clave"
    )
    is_active = models.BooleanField(default=True)

    def __str__(self): return self.name

# --- 2. GESTIÓN LEGISLATIVA (SUTRA & COMPARADOR) ---
class Bill(models.Model):
    number = models.CharField(max_length=50, unique=True) # Ej: P. de la C. 1001
    title = models.TextField()
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self): return self.number

class BillVersion(models.Model):
    bill = models.ForeignKey(Bill, related_name='versions', on_delete=models.CASCADE)
    version_name = models.CharField(max_length=100) # Ej: Entirillado, Aprobado
    pdf_file = models.FileField(upload_to='bills_pdfs/')
    full_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # 1. Guardar el archivo primero
        super().save(*args, **kwargs)
        
        # 2. Extraer texto automáticamente según el formato
        if self.pdf_file and not self.full_text:
            try:
                file_path = self.pdf_file.path
                extracted_text = ""
                
                # A. SI ES PDF
                if file_path.lower().endswith('.pdf'):
                    reader = PdfReader(file_path)
                    for page in reader.pages:
                        text = page.extract_text()
                        if text: extracted_text += text + "\n"
                
                # B. SI ES WORD (.DOCX) - NUEVO
                elif file_path.lower().endswith('.docx'):
                    doc = docx.Document(file_path)
                    for para in doc.paragraphs:
                        if para.text: extracted_text += para.text + "\n"
                
                # Guardar el texto extraído
                if extracted_text:
                    self.full_text = extracted_text
                    super().save(update_fields=['full_text'])
                    
            except Exception as e:
                print(f"Error leyendo archivo {self.pdf_file.name}: {e}")

    def __str__(self): return f"{self.bill.number} - {self.version_name}"

# --- 3. CONFIGURACIÓN Y MONITOREO ---
class SystemSettings(models.Model):
    """Configuración del servicio de monitoreo automático"""
    is_active = models.BooleanField(default=True, help_text="Activar/desactivar el servicio globalmente")
    active_days = models.CharField(max_length=50, default="0,1,2,3,4", help_text="Días activos: 0=Lunes, 6=Domingo")
    high_freq_start = models.TimeField(default=time(8, 0), help_text="Inicio del horario intensivo")
    high_freq_end = models.TimeField(default=time(17, 0), help_text="Fin del horario intensivo")
    high_freq_interval = models.IntegerField(default=15, help_text="Intervalo en modo intensivo (minutos)")
    low_freq_interval = models.IntegerField(default=120, help_text="Intervalo en modo pasivo (minutos)")
    
    class Meta:
        verbose_name = "Configuración del Sistema"
        verbose_name_plural = "Configuración del Sistema"
    
    def __str__(self):
        return f"Config Sistema ({'Activo' if self.is_active else 'Pausado'})"

class Keyword(models.Model):
    term = models.CharField(max_length=100)
    def __str__(self): return self.term

class MonitoredMeasure(models.Model):
    sutra_id = models.CharField(max_length=50) # Ej: P. de la C. 1234
    added_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.sutra_id

class MonitoredCommission(models.Model):
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    def __str__(self): return self.name

# --- 4. PERFILES DE USUARIO ---
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    webhook_measures = models.URLField(max_length=500, blank=True, null=True, verbose_name="Webhook Medidas")
    webhook_commissions = models.URLField(max_length=500, blank=True, null=True, verbose_name="Webhook Comisiones")
    webhook_keywords = models.URLField(max_length=500, blank=True, null=True, verbose_name="Webhook Keywords")
    webhook_general = models.URLField(max_length=500, blank=True, null=True, verbose_name="Webhook General")
    
    def __str__(self):
        return f"Perfil de {self.user.username}"

# --- 5. AGENDA / CALENDARIO ---
class Event(models.Model):
    title = models.CharField(max_length=200)
    date = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    
    def __str__(self): return self.title