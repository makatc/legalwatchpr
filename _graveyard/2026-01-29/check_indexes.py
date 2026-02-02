"""
Script para verificar el estado de índices de búsqueda híbrida
Ejecutar: python manage.py shell < check_indexes.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

print("\n" + "="*70)
print("VERIFICACIÓN DE ÍNDICES DE BÚSQUEDA HÍBRIDA")
print("="*70 + "\n")

with connection.cursor() as cursor:
    # 1. Verificar que los campos existen
    print("📋 VERIFICANDO CAMPOS EN LA TABLA core_article:\n")
    
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'core_article' 
        AND column_name IN ('search_vector', 'embedding')
        ORDER BY column_name;
    """)
    
    fields = cursor.fetchall()
    if fields:
        for field_name, data_type, is_nullable in fields:
            print(f"  ✅ {field_name:20} | Tipo: {data_type:20} | NULL: {is_nullable}")
    else:
        print("  ❌ Los campos search_vector y embedding NO EXISTEN")
        print("     Ejecuta: python manage.py migrate")
    
    # 2. Verificar índices creados
    print("\n" + "="*70)
    print("📊 VERIFICANDO ÍNDICES:\n")
    
    cursor.execute("""
        SELECT 
            indexname,
            indexdef,
            pg_size_pretty(pg_relation_size(indexname::regclass)) as size
        FROM pg_indexes
        WHERE tablename = 'core_article'
        AND indexname LIKE 'idx_article_%'
        ORDER BY indexname;
    """)
    
    indexes = cursor.fetchall()
    if indexes:
        for idx_name, idx_def, idx_size in indexes:
            icon = "✅" if "search_vector" in idx_def or "embedding" in idx_def else "📌"
            print(f"{icon} {idx_name}")
            print(f"   Tamaño: {idx_size}")
            print(f"   Definición: {idx_def[:100]}...")
            print()
    else:
        print("  ⚠️  No se encontraron índices de búsqueda híbrida")
    
    # 3. Estadísticas de datos
    print("="*70)
    print("📈 ESTADÍSTICAS DE DATOS:\n")
    
    # Verificar si el campo embedding existe primero
    cursor.execute("""
        SELECT EXISTS(
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'core_article' AND column_name = 'embedding'
        );
    """)
    embedding_exists = cursor.fetchone()[0]
    
    if embedding_exists:
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(search_vector) as con_search_vector,
                COUNT(embedding) as con_embedding
            FROM core_article;
        """)
        
        total, with_sv, with_emb = cursor.fetchone()
        print(f"  Total de artículos:              {total:>6}")
        print(f"  Con search_vector generado:      {with_sv:>6} ({with_sv*100//max(total,1):>3}%)")
        print(f"  Con embedding generado:          {with_emb:>6} ({with_emb*100//max(total,1):>3}%)")
    else:
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(search_vector) as con_search_vector
            FROM core_article;
        """)
        
        total, with_sv = cursor.fetchone()
        print(f"  Total de artículos:              {total:>6}")
        print(f"  Con search_vector generado:      {with_sv:>6} ({with_sv*100//max(total,1):>3}%)")
        print("  Campo embedding:                 NO CREADO (pgvector no disponible)")
    
    # 4. Verificar extensiones necesarias
    print("\n" + "="*70)
    print("🔧 EXTENSIONES POSTGRESQL:\n")
    
    cursor.execute("SELECT extname, extversion FROM pg_extension WHERE extname IN ('vector', 'unaccent');")
    extensions = cursor.fetchall()
    
    ext_dict = {name: version for name, version in extensions}
    
    if 'vector' in ext_dict:
        print(f"  ✅ pgvector: v{ext_dict['vector']}")
    else:
        print("  ⚠️  pgvector: NO INSTALADO (índice HNSW no disponible)")
    
    if 'unaccent' in ext_dict:
        print(f"  ✅ unaccent: v{ext_dict['unaccent']}")
    else:
        print("  ❌ unaccent: NO INSTALADO")
    
    # 5. Recomendaciones
    print("\n" + "="*70)
    print("💡 PRÓXIMOS PASOS:\n")
    
    if not fields:
        print("  1. Ejecutar migración: python manage.py migrate")
    elif with_sv == 0 and total > 0:
        print("  1. Generar search_vectors: python populate_search_vectors.py")
    
    if 'vector' in ext_dict and embedding_exists:
        if 'with_emb' in locals() and with_emb == 0 and total > 0:
            print("  2. Generar embeddings: python populate_embeddings.py")
        
        cursor.execute("SELECT indexname FROM pg_indexes WHERE indexname = 'idx_article_embedding_hnsw';")
        if not cursor.fetchone():
            print("  3. Crear índice HNSW: psql < sql/create_hnsw_index.sql")
    elif not embedding_exists:
        print("  2. Campo embedding no creado (pgvector no instalado)")
        print("     Ver INSTALL_PGVECTOR.md para instalar pgvector")
    
    print("\n" + "="*70 + "\n")
