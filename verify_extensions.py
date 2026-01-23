"""
Script de verificación de extensiones PostgreSQL
Ejecutar: python manage.py shell < verify_extensions.py
"""
from django.db import connection

def verify_postgres_extensions():
    """Verifica que las extensiones necesarias estén instaladas en PostgreSQL."""
    
    print("\n🔍 VERIFICANDO EXTENSIONES POSTGRESQL\n" + "="*50)
    
    with connection.cursor() as cursor:
        # Verificar extensión pgvector
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM pg_extension WHERE extname = 'vector'
            );
        """)
        pgvector_installed = cursor.fetchone()[0]
        
        # Verificar extensión unaccent
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM pg_extension WHERE extname = 'unaccent'
            );
        """)
        unaccent_installed = cursor.fetchone()[0]
        
        # Verificar configuración de texto español
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM pg_ts_config WHERE cfgname = 'spanish'
            );
        """)
        spanish_config = cursor.fetchone()[0]
        
        # Verificar versión de pgvector (si está instalado)
        pgvector_version = None
        if pgvector_installed:
            cursor.execute("""
                SELECT extversion FROM pg_extension WHERE extname = 'vector';
            """)
            pgvector_version = cursor.fetchone()[0]
        
        # Mostrar resultados
        print(f"\n✅ pgvector: {'INSTALADO' if pgvector_installed else '❌ NO INSTALADO'}")
        if pgvector_version:
            print(f"   Versión: {pgvector_version}")
        
        print(f"\n✅ unaccent: {'INSTALADO' if unaccent_installed else '❌ NO INSTALADO'}")
        print(f"\n✅ Spanish text search: {'DISPONIBLE' if spanish_config else '❌ NO DISPONIBLE'}")
        
        # Verificar tipo de datos vector (solo si pgvector está instalado)
        if pgvector_installed:
            cursor.execute("""
                SELECT EXISTS(
                    SELECT 1 FROM pg_type WHERE typname = 'vector'
                );
            """)
            vector_type = cursor.fetchone()[0]
            print(f"\n✅ Tipo de dato 'vector': {'DISPONIBLE' if vector_type else '❌ NO DISPONIBLE'}")
        
        print("\n" + "="*50)
        
        # Resumen
        all_ok = pgvector_installed and unaccent_installed and spanish_config
        if all_ok:
            print("\n🎉 TODAS LAS EXTENSIONES ESTÁN CORRECTAMENTE INSTALADAS\n")
        else:
            print("\n⚠️ FALTAN EXTENSIONES - Ejecuta: python manage.py migrate\n")
        
        return all_ok

if __name__ == '__main__':
    verify_postgres_extensions()
