# Script de instalación de pgvector para PostgreSQL 18 en Windows
# Este script copia manualmente los archivos de pgvector

$POSTGRES_PATH = "C:\Program Files\PostgreSQL\18"
$TEMP_PGVECTOR = "$env:TEMP\pgvector"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "INSTALACIÓN DE PGVECTOR PARA POSTGRESQL 18" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Verificar que PostgreSQL existe
if (-not (Test-Path $POSTGRES_PATH)) {
    Write-Host "ERROR: PostgreSQL 18 no encontrado en $POSTGRES_PATH" -ForegroundColor Red
    exit 1
}

Write-Host "✓ PostgreSQL 18 encontrado: $POSTGRES_PATH" -ForegroundColor Green

# Verificar que tenemos el código fuente de pgvector
if (-not (Test-Path $TEMP_PGVECTOR)) {
    Write-Host "ERROR: Código fuente de pgvector no encontrado en $TEMP_PGVECTOR" -ForegroundColor Red
    Write-Host "Ejecuta primero: git clone https://github.com/pgvector/pgvector.git $TEMP_PGVECTOR" -ForegroundColor Yellow
    exit 1
}

Write-Host "✓ Código fuente de pgvector encontrado" -ForegroundColor Green

# Para Windows, necesitamos copiar manualmente los archivos SQL y control
# La compilación del .dll requiere Visual Studio, así que intentaremos sin él primero

Write-Host "`nCopiando archivos de control y SQL..." -ForegroundColor Yellow

$EXTENSION_DIR = "$POSTGRES_PATH\share\extension"

# Copiar archivos .control
Copy-Item "$TEMP_PGVECTOR\vector.control" -Destination $EXTENSION_DIR -Force
Write-Host "✓ Copiado vector.control" -ForegroundColor Green

# Copiar todos los archivos SQL de actualización
$sqlFiles = Get-ChildItem "$TEMP_PGVECTOR\sql" -Filter "vector--*.sql"
foreach ($file in $sqlFiles) {
    Copy-Item $file.FullName -Destination $EXTENSION_DIR -Force
    Write-Host "✓ Copiado $($file.Name)" -ForegroundColor Green
}

Write-Host "`n⚠ NOTA IMPORTANTE:" -ForegroundColor Yellow
Write-Host "pgvector requiere un archivo .dll compilado (vector.dll)" -ForegroundColor Yellow
Write-Host "Este archivo requiere Visual Studio para compilarse.`n" -ForegroundColor Yellow

Write-Host "OPCIONES DISPONIBLES:" -ForegroundColor Cyan
Write-Host "1. Descargar vector.dll precompilado de una fuente confiable" -ForegroundColor White
Write-Host "2. Compilar con Visual Studio Build Tools (requiere instalación)" -ForegroundColor White
Write-Host "3. Usar PostgreSQL con pgvector vía Docker (recomendado)" -ForegroundColor White

Write-Host "`nBuscando vector.dll precompilado en GitHub releases..." -ForegroundColor Yellow

# Intentar descargar desde releases si existe
$releases_url = "https://github.com/pgvector/pgvector/releases"
Write-Host "Visita manualmente: $releases_url" -ForegroundColor White
Write-Host "Busca: vector-<version>-pg18-windows-x64.zip o similar`n" -ForegroundColor White

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "INSTALACIÓN PARCIAL COMPLETADA" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Archivos copiados:" -ForegroundColor Green
Write-Host "  ✓ vector.control" -ForegroundColor Green
Write-Host "  ✓ vector--*.sql (archivos de migración)" -ForegroundColor Green
Write-Host "`n⚠ FALTA: vector.dll (requiere compilación o descarga)" -ForegroundColor Yellow

Write-Host "`nPara completar la instalación, ejecuta uno de estos comandos:`n" -ForegroundColor Cyan
Write-Host "OPCIÓN 1 - Compilar con nmake (requiere Visual Studio):" -ForegroundColor Yellow
Write-Host "  cd $TEMP_PGVECTOR" -ForegroundColor White
Write-Host '  "C:\Program Files\PostgreSQL\18\bin\pg_config" --version' -ForegroundColor White
Write-Host "  nmake /F Makefile.win" -ForegroundColor White
Write-Host "  nmake /F Makefile.win install`n" -ForegroundColor White

Write-Host "OPCIÓN 2 - Usar Docker PostgreSQL con pgvector (MÁS FÁCIL):" -ForegroundColor Yellow
Write-Host "  Ver: install_pgvector_docker.ps1`n" -ForegroundColor White
