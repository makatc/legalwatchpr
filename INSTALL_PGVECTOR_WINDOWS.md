# GUÍA DE INSTALACIÓN DE PGVECTOR EN POSTGRESQL 18 WINDOWS

## 📋 PASOS A SEGUIR

### PASO 1: Ejecutar PowerShell como Administrador

1. Presiona `Windows + X`
2. Selecciona "Windows PowerShell (Administrador)" o "Terminal (Administrador)"
3. Confirma el UAC (Control de cuentas de usuario)

### PASO 2: Navegar al proyecto

```powershell
cd C:\Users\becof\vs\legalwatchpr
```

### PASO 3: Ejecutar el instalador

```powershell
.\install_pgvector_admin.ps1
```

Este script hará:
- ✅ Copiar archivos `.control` y `.sql` de pgvector
- ⚠️ Intentar descargar `vector.dll` automáticamente
- ℹ️ Mostrar instrucciones si la descarga falla

---

## ⚡ ALTERNATIVA RÁPIDA: Descarga Manual del DLL

Si el script no descarga automáticamente el DLL:

### Opción A: Usar binarios de PG16 (compatible)

1. Ve a: https://github.com/pgvector/pgvector/releases/download/v0.8.0/pgvector-v0.8.0-pg16-windows-x64.zip

2. Descarga el archivo ZIP

3. Extrae `vector.dll` del ZIP

4. Copia `vector.dll` a:
   ```
   C:\Program Files\PostgreSQL\18\lib\
   ```

5. Reinicia PostgreSQL:
   ```powershell
   Restart-Service postgresql-x64-18
   ```

### Opción B: Compilar desde código fuente (requiere Visual Studio)

Solo si realmente quieres compilar tú mismo:

1. Instala Visual Studio Build Tools: https://visualstudio.microsoft.com/downloads/

2. Abre "Developer Command Prompt for VS 2022"

3. Ejecuta:
   ```cmd
   cd %TEMP%\pgvector
   "C:\Program Files\PostgreSQL\18\bin\pg_config" --version
   nmake /F Makefile.win
   nmake /F Makefile.win install
   ```

---

## ✅ VERIFICAR INSTALACIÓN

Después de copiar los archivos, verifica que pgvector funcione:

```powershell
python install_extensions.py
```

Deberías ver:
```
✅ unaccent instalado correctamente
✅ pgvector instalado correctamente
```

Luego ejecuta:
```powershell
python check_db.py
```

Deberías ver:
```
✅ pgvector: INSTALADO
   Versión: 0.8.0
```

---

## 🔄 SIGUIENTE PASO: Aplicar Migraciones

Una vez que pgvector esté instalado:

```powershell
python manage.py migrate
python check_indexes.py
```

Deberías ver:
```
✅ search_vector: CREADO
✅ embedding: CREADO (384 dimensiones)
✅ idx_article_search_vector: CREADO (GIN)
```

---

## 🆘 SOLUCIÓN DE PROBLEMAS

### Error: "extension 'vector' is not available"

**Causa:** Los archivos no se copiaron correctamente o PostgreSQL no se reinició.

**Solución:**
1. Verifica que `vector.dll` existe en `C:\Program Files\PostgreSQL\18\lib\`
2. Verifica que `vector.control` existe en `C:\Program Files\PostgreSQL\18\share\extension\`
3. Reinicia PostgreSQL: `Restart-Service postgresql-x64-18`

### Error: "Access denied" al copiar archivos

**Causa:** PowerShell no tiene permisos de administrador.

**Solución:**
- Cierra PowerShell
- Abre PowerShell como Administrador
- Ejecuta nuevamente el script

### PostgreSQL no se puede reiniciar

**Causa:** Puede haber un problema con el DLL.

**Solución:**
1. Abre Services (services.msc)
2. Busca "postgresql-x64-18"
3. Haz clic derecho > Reiniciar
4. Si falla, revisa logs en `C:\Program Files\PostgreSQL\18\data\log\`

---

## 📞 ALTERNATIVA FINAL: Docker

Si todo lo anterior falla, la forma más fácil es usar PostgreSQL con pgvector en Docker:

```powershell
# Instalar Docker Desktop para Windows primero
# Luego ejecutar:
docker run -d \
  --name postgres-pgvector \
  -e POSTGRES_PASSWORD=tu_password \
  -e POSTGRES_DB=legalwatchpr_db \
  -p 5432:5432 \
  ankane/pgvector

# Actualizar .env con la nueva conexión
# Ejecutar migraciones
python manage.py migrate
```

Docker ya incluye pgvector preinstalado y funcionando.
