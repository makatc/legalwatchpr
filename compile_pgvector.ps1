# Script para compilar pgvector usando MSYS2/MinGW

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "COMPILADOR DE PGVECTOR PARA POSTGRESQL 18" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$PG_PATH = "C:\Program Files\PostgreSQL\18"
$PG_BIN = "$PG_PATH\bin"
$PG_LIB = "$PG_PATH\lib"
$PG_INCLUDE = "$PG_PATH\include\server"
$TEMP_PGVECTOR = "$env:TEMP\pgvector"

Write-Host "Verificando PostgreSQL..." -ForegroundColor Yellow
if (-not (Test-Path "$PG_BIN\pg_config.exe")) {
    Write-Host "ERROR: pg_config.exe no encontrado" -ForegroundColor Red
    exit 1
}
Write-Host "PostgreSQL 18 encontrado" -ForegroundColor Green

Write-Host ""
Write-Host "Descargando MinGW64..." -ForegroundColor Yellow
$mingwUrl = "https://github.com/niXman/mingw-builds-binaries/releases/download/14.2.0-rt_v12-rev0/x86_64-14.2.0-release-posix-seh-msvcrt-rt_v12-rev0.7z"
$mingwZip = "$env:TEMP\mingw64.7z"

try {
    Invoke-WebRequest -Uri $mingwUrl -OutFile $mingwZip -ErrorAction Stop
    Write-Host "MinGW descargado" -ForegroundColor Green
} catch {
    Write-Host "ERROR: No se pudo descargar MinGW" -ForegroundColor Red
    Write-Host "URL: $mingwUrl" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Extrayendo MinGW..." -ForegroundColor Yellow
$mingwDir = "$env:TEMP\mingw64"

if (Get-Command 7z -ErrorAction SilentlyContinue) {
    7z x $mingwZip -o"$env:TEMP" -y | Out-Null
    Write-Host "MinGW extraido" -ForegroundColor Green
} else {
    Write-Host "ERROR: Se requiere 7-Zip para extraer MinGW" -ForegroundColor Red
    Write-Host "Instala 7-Zip desde: https://www.7-zip.org/" -ForegroundColor Yellow
    Write-Host "O usa: winget install 7zip.7zip" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Compilando pgvector..." -ForegroundColor Yellow
cd $TEMP_PGVECTOR

$env:PATH = "$mingwDir\bin;$PG_BIN;$env:PATH"
$env:PG_CONFIG = "$PG_BIN\pg_config.exe"

try {
    & "$mingwDir\bin\mingw32-make.exe" clean 2>&1 | Out-Null
    & "$mingwDir\bin\mingw32-make.exe" PG_CONFIG="$PG_BIN\pg_config.exe" 2>&1 | Out-Null
    
    if (Test-Path "$TEMP_PGVECTOR\vector.dll") {
        Write-Host "Compilacion exitosa" -ForegroundColor Green
        
        Write-Host ""
        Write-Host "Instalando vector.dll..." -ForegroundColor Yellow
        Copy-Item "$TEMP_PGVECTOR\vector.dll" -Destination $PG_LIB -Force
        Write-Host "vector.dll instalado" -ForegroundColor Green
        
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "INSTALACION COMPLETADA CON EXITO" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        
        Write-Host "Reiniciando PostgreSQL..." -ForegroundColor Yellow
        try {
            Restart-Service postgresql-x64-18 -ErrorAction Stop
            Write-Host "PostgreSQL reiniciado" -ForegroundColor Green
        } catch {
            Write-Host "Reinicia manualmente PostgreSQL" -ForegroundColor Yellow
        }
        
        Write-Host ""
        Write-Host "PROXIMOS PASOS:" -ForegroundColor Cyan
        Write-Host "1. python install_extensions.py" -ForegroundColor White
        Write-Host "2. python check_db.py" -ForegroundColor White
        Write-Host ""
        
    } else {
        Write-Host "ERROR: Compilacion fallida" -ForegroundColor Red
        Write-Host "No se genero vector.dll" -ForegroundColor Yellow
    }
} catch {
    Write-Host "ERROR durante compilacion: $($_.Exception.Message)" -ForegroundColor Red
}
