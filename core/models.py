from datetime import time
import hashlib
import docx
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from pypdf import PdfReader
from pgvector.django import VectorField
from django.contrib.auth.models import User

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
    content_hash = models.CharField(max_length=32, blank=True, null=True)
    relevance_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    search_vector = SearchVectorField(null=True, blank=True)
    
    # Campo para IA (384 dimensiones para MiniLM)
    embedding = VectorField(dimensions=384, null=True, blank=True)
    
    class Meta:
        ordering = ['-published_at']
        indexes = [GinIndex(fields=['search_vector'], name='idx_article_search_vector')]
    
    def save(self, *args, **kwargs):
        if self.snippet:
            self.content_hash = hashlib.md5(self.snippet.encode('utf-8')).hexdigest()
        super().save(*args, **kwargs)
    def __str__(self): return self.title

class NewsPreset(models.Model):
    SEARCH_METHOD_CHOICES = [('hybrid', 'Híbrida'), ('semantic', 'Semántica'), ('keyword', 'Léxica')]
    name = models.CharField(max_length=100)
    keywords = models.TextField()
    threshold = models.IntegerField(default=15)
    fields_to_analyze = models.CharField(max_length=100, default="title,description")
    search_method = models.CharField(max_length=20, choices=SEARCH_METHOD_CHOICES, default='hybrid')
    is_active = models.BooleanField(default=True)
    def __str__(self): return self.name

# --- 2. GESTIÓN LEGISLATIVA (SUTRA) ---
class Bill(models.Model):
    number = models.CharField(max_length=50, unique=True)
    title = models.TextField()
    last_updated = models.DateTimeField(auto_now=True)
    def __str__(self): return self.number

class BillVersion(models.Model):
    bill = models.ForeignKey(Bill, related_name='versions', on_delete=models.CASCADE)
    version_name = models.CharField(max_length=100)
    pdf_file = models.FileField(upload_to='bills_pdfs/')
    full_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.pdf_file and not self.full_text:
            try:
                extracted_text = ""
                if self.pdf_file.path.lower().endswith('.pdf'):
                    reader = PdfReader(self.pdf_file.path)
                    for page in reader.pages: extracted_text += (page.extract_text() or "")
                elif self.pdf_file.path.lower().endswith('.docx'):
                    doc = docx.Document(self.pdf_file.path)
                    for para in doc.paragraphs: extracted_text += para.text + "\n"
                if extracted_text:
                    self.full_text = extracted_text
                    super().save(update_fields=['full_text'])
            except Exception as e: print(f"Error: {e}")
    def __str__(self): return f"{self.bill.number} - {self.version_name}"

class SystemSettings(models.Model):
    is_active = models.BooleanField(default=True)
    active_days = models.CharField(max_length=50, default="0,1,2,3,4")
    high_freq_start = models.TimeField(default=time(8, 0))
    high_freq_end = models.TimeField(default=time(17, 0))
    high_freq_interval = models.IntegerField(default=15)
    low_freq_interval = models.IntegerField(default=120)
    class Meta:
        verbose_name = "Configuración del Sistema"
    def __str__(self): return "Config Global"

class MonitoredMeasure(models.Model):
    sutra_id = models.CharField(max_length=50)
    keywords = models.TextField(blank=True, default="")
    threshold = models.IntegerField(default=15)
    search_method = models.CharField(max_length=20, choices=[('hybrid', 'Híbrida'), ('semantic', 'Semántica'), ('keyword', 'Léxica')], default='hybrid')
    is_active = models.BooleanField(default=True)
    added_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.sutra_id

class MonitoredCommission(models.Model):
    name = models.CharField(max_length=200)
    keywords = models.TextField(blank=True, default="")
    threshold = models.IntegerField(default=15)
    search_method = models.CharField(max_length=20, choices=[('hybrid', 'Híbrida')], default='hybrid')
    is_active = models.BooleanField(default=True)
    def __str__(self): return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    webhook_general = models.URLField(max_length=500, blank=True, null=True)
    def __str__(self): return self.user.username

class Event(models.Model):
    title = models.CharField(max_length=200)
    date = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    def __str__(self): return self.title