import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

print("\nInstalando extensiones PostgreSQL...\n")

with connection.cursor() as cursor:
    try:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS unaccent;")
        print("✅ unaccent instalado correctamente")
    except Exception as e:
        print(f"❌ Error instalando unaccent: {e}")
    
    try:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        print("✅ pgvector instalado correctamente")
    except Exception as e:
        print(f"⚠️ pgvector no disponible: {e}")
        print("   Ver INSTALL_PGVECTOR.md para instrucciones de instalación")

print("\nVerificando instalación...\n")

with connection.cursor() as cursor:
    cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'unaccent')")
    unaccent = cursor.fetchone()[0]
    print(f"{'✅' if unaccent else '❌'} unaccent: {'INSTALADO' if unaccent else 'NO INSTALADO'}")
    
    cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')")
    pgvector = cursor.fetchone()[0]
    print(f"{'✅' if pgvector else '❌'} pgvector: {'INSTALADO' if pgvector else 'NO INSTALADO'}")

print()
