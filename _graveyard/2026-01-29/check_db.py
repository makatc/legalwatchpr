import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

print("\n" + "="*50)
print("VERIFICACION DE EXTENSIONES POSTGRESQL")
print("="*50 + "\n")

with connection.cursor() as cursor:
    # Verificar pgvector
    cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')")
    pgvector = cursor.fetchone()[0]
    print(f"{'✅' if pgvector else '❌'} pgvector: {'INSTALADO' if pgvector else 'NO INSTALADO'}")
    
    # Verificar unaccent
    cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'unaccent')")
    unaccent = cursor.fetchone()[0]
    print(f"{'✅' if unaccent else '❌'} unaccent: {'INSTALADO' if unaccent else 'NO INSTALADO'}")
    
    # Verificar config español
    cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_ts_config WHERE cfgname = 'spanish')")
    spanish = cursor.fetchone()[0]
    print(f"{'✅' if spanish else '❌'} Spanish text search: {'DISPONIBLE' if spanish else 'NO DISPONIBLE'}")

print("\n" + "="*50 + "\n")
