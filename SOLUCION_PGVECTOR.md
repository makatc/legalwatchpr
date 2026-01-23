# Guía para usar PostgreSQL con pgvector en Docker

## Opción 1: Docker (MÁS RÁPIDO Y CONFIABLE)

### 1. Instala Docker Desktop para Windows
```powershell
winget install Docker.DockerDesktop
```

### 2. Detén PostgreSQL local temporalmente
```powershell
Stop-Service postgresql-x64-18
```

### 3. Crea contenedor PostgreSQL con pgvector
```powershell
docker run -d `
  --name postgres-pgvector `
  -e POSTGRES_PASSWORD=tu_contraseña `
  -e POSTGRES_DB=legalwatchpr_db `
  -p 5432:5432 `
  -v pgvector_data:/var/lib/postgresql/data `
  pgvector/pgvector:pg18
```

### 4. Actualiza tu .env o settings.py
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'legalwatchpr_db',
        'USER': 'postgres',
        'PASSWORD': 'tu_contraseña',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 5. Aplica migraciones
```powershell
python manage.py migrate
python check_db.py  # Verificar que pgvector esté disponible
```

### 6. ¡Listo! pgvector funcionando

---

## Opción 2: Descargar DLL precompilado manualmente

Si prefieres seguir usando PostgreSQL 18 local:

### 1. Descarga el DLL manualmente
Visita: https://pgxn.org/dist/vector/
O contacta al mantenedor de pgvector para obtener un DLL compatible con PostgreSQL 18

### 2. Copia el DLL
```powershell
Copy-Item vector.dll -Destination "C:\Program Files\PostgreSQL\18\lib\" -Force
```

### 3. Reinicia PostgreSQL
```powershell
Restart-Service postgresql-x64-18
```

### 4. Habilita la extensión
```powershell
python install_extensions.py
```

---

## Opción 3: Compilar con Visual Studio (Avanzado)

### Requisitos:
- Visual Studio 2022 con herramientas de C++
- PostgreSQL 18 development files

### Pasos:
```powershell
# 1. Instala Visual Studio Build Tools
winget install Microsoft.VisualStudio.2022.BuildTools

# 2. Abre "Developer Command Prompt for VS 2022"

# 3. Compila pgvector
cd %TEMP%\pgvector
nmake /f Makefile.win

# 4. Copia el DLL generado
copy vector.dll "C:\Program Files\PostgreSQL\18\lib\"

# 5. Reinicia PostgreSQL
net stop postgresql-x64-18 && net start postgresql-x64-18
```

---

## ¿Cuál opción recomiendo?

**Docker (Opción 1)** es la mejor para desarrollo:
- ✅ Instalación en 5 minutos
- ✅ pgvector garantizado funcional
- ✅ Fácil de resetear/actualizar
- ✅ No requiere compilación
- ✅ Mismo resultado en producción

**DLL manual (Opción 2)** si:
- Ya tienes el DLL de otra fuente
- Necesitas usar PostgreSQL 18 local obligatoriamente

**Compilar (Opción 3)** solo si:
- Necesitas una versión específica personalizada
- Contribuirás código a pgvector
