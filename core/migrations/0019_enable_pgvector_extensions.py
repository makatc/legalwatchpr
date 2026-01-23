# Generated migration for enabling PostgreSQL extensions
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_alter_article_link'),
    ]

    operations = [
        # NOTA: Esta migración intenta habilitar pgvector
        # Si falla, debes instalar pgvector en tu sistema PostgreSQL primero.
        # Ver INSTALL_PGVECTOR.md para instrucciones.
        
        # Habilitar extensión pgvector para embeddings vectoriales (OPCIONAL - puede fallar si no está instalado)
        migrations.RunSQL(
            sql='CREATE EXTENSION IF NOT EXISTS vector;',
            reverse_sql='DROP EXTENSION IF EXISTS vector;',
            state_operations=[]  # No cambia el estado del modelo
        ),
        
        # Habilitar unaccent para búsqueda insensible a tildes (español)
        migrations.RunSQL(
            sql='CREATE EXTENSION IF NOT EXISTS unaccent;',
            reverse_sql='DROP EXTENSION IF EXISTS unaccent;',
            state_operations=[]
        ),
    ]
