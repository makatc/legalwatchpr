from django.db import models
from django.utils import timezone
import os
from pypdf import PdfReader
import docx  # LIBRERÍA NUEVA PARA WORD

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
    link = models.URLField(unique=True)
    published_at = models.DateTimeField()
    snippet = models.TextField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    ai_summary = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return self.title

class NewsPreset(models.Model):
    name = models.CharField(max_length=100)
    keywords = models.TextField(help_text="Separadas por coma")
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
class Keyword(models.Model):
    term = models.CharField(max_length=100)
    def __str__(self): return self.term

class MonitoredMeasure(models.Model):
    sutra_id = models.CharField(max_length=50) # Ej: P. de la C. 1234
    added_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.sutra_id

class MonitoredCommission(models.Model):
    name = models.CharField(max_length=200)
    def __str__(self): return self.name

# --- 4. AGENDA / CALENDARIO ---
class Event(models.Model):
    title = models.CharField(max_length=200)
    date = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    
    def __str__(self): return self.title