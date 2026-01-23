# Instalación de pgvector para PostgreSQL

## ¿Qué es pgvector?

`pgvector` es una extensión de PostgreSQL que permite almacenar y buscar vectores de embeddings (representaciones numéricas de texto) directamente en la base de datos. Es esencial para búsqueda semántica avanzada.

---

## Instalación en Windows

### Opción 1: Docker PostgreSQL con pgvector (RECOMENDADO)

La forma más sencilla es usar una imagen Docker que ya incluye pgvector:

```powershell
# Detener PostgreSQL actual (si está corriendo localmente)
# Luego iniciar contenedor con pgvector
docker run -d \
  --name postgres-pgvector \
  -e POSTGRES_PASSWORD=tu_password \
  -e POSTGRES_DB=legalwatchpr \
  -p 5432:5432 \
  ankane/pgvector
```

Actualiza tu `.env` o `settings.py` con la nueva conexión:
```
DATABASE_URL=postgresql://postgres:tu_password@localhost:5432/legalwatchpr
```

### Opción 2: Instalar pgvector en PostgreSQL existente

Si ya tienes PostgreSQL instalado en Windows:

1. **Descargar binarios de pgvector para Windows:**
   - Ve a: https://github.com/pgvector/pgvector/releases
   - Descarga el archivo `.dll` para tu versión de PostgreSQL

2. **Copiar extensión a carpeta de PostgreSQL:**
   ```powershell
   # Ubica tu instalación de PostgreSQL (ejemplo: C:\Program Files\PostgreSQL\15\)
   # Copia vector.dll a: C:\Program Files\PostgreSQL\15\lib\
   # Copia vector.control y vector--*.sql a: C:\Program Files\PostgreSQL\15\share\extension\
   ```

3. **Reiniciar PostgreSQL:**
   ```powershell
   # Desde Services (services.msc) reinicia el servicio postgresql-x64-15
   ```

### Opción 3: Compilar desde código fuente (Avanzado)

Requiere Visual Studio Build Tools y herramientas de desarrollo:

```powershell
git clone https://github.com/pgvector/pgvector.git
cd pgvector
# Seguir instrucciones en README para Windows
```

---

## Instalación en Linux/Mac

```bash
# Ubuntu/Debian
sudo apt install postgresql-contrib postgresql-server-dev-all
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install

# macOS (con Homebrew)
brew install pgvector
```

---

## Verificación de Instalación

Una vez instalada la extensión en PostgreSQL, ejecuta:

```bash
python manage.py migrate
python verify_extensions.py
```

Si la instalación fue exitosa, verás:
```
✅ pgvector: INSTALADO
   Versión: 0.5.0
✅ unaccent: INSTALADO
✅ Spanish text search: DISPONIBLE
```

---

## Solución de Problemas

### Error: "extension 'vector' is not available"

**Causa:** La extensión no está instalada en el servidor PostgreSQL.

**Solución:**
1. Verifica que los archivos de extensión existan:
   ```sql
   SELECT * FROM pg_available_extensions WHERE name = 'vector';
   ```
   
2. Si no aparece, instala pgvector siguiendo las opciones arriba.

3. Si tienes privilegios de superusuario:
   ```sql
   CREATE EXTENSION vector;
   ```

### Error: "permission denied to create extension"

**Causa:** El usuario de la base de datos no tiene permisos de superusuario.

**Solución:**
```sql
-- Como superusuario de PostgreSQL
GRANT CREATE ON DATABASE legalwatchpr TO tu_usuario;
-- O crear la extensión manualmente:
CREATE EXTENSION IF NOT EXISTS vector;
```

---

## Alternativa: Usar BM25 sin pgvector

Si no puedes instalar pgvector, el sistema **ya funciona** usando el algoritmo BM25 para relevancia semántica. pgvector es **opcional** y mejora la precisión de búsquedas, pero **no es obligatorio** para que la aplicación funcione.

Para desactivar funcionalidades que requieren pgvector:
- Comenta la migración `0019_enable_pgvector_extensions.py`
- No uses campos `VectorField` en modelos

---

## Próximos Pasos

Una vez instalado pgvector, podrás:
- Generar embeddings de artículos con `sentence-transformers`
- Buscar artículos similares por contenido semántico
- Implementar recomendaciones basadas en IA
- Mejorar la precisión del sistema de filtros
