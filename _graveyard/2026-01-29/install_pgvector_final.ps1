Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "INSTALADOR DE PGVECTOR PARA POSTGRESQL 18" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$TEMP_PGVECTOR = "$env:TEMP\pgvector"
$PG_PATH = "C:\Program Files\PostgreSQL\18"
$EXTENSION_DIR = "$PG_PATH\share\extension"
$LIB_DIR = "$PG_PATH\lib"

if (-not (Test-Path $PG_PATH)) {
    Write-Host "ERROR: PostgreSQL 18 no encontrado en $PG_PATH" -ForegroundColor Red
    exit 1
}
Write-Host "PostgreSQL 18 encontrado" -ForegroundColor Green

if (-not (Test-Path $TEMP_PGVECTOR)) {
    Write-Host ""
    Write-Host "Clonando repositorio de pgvector..." -ForegroundColor Yellow
    Set-Location $env:TEMP
    git clone --branch v0.8.0 https://github.com/pgvector/pgvector.git 2>&1 | Out-Null
}
Write-Host "Codigo fuente de pgvector disponible" -ForegroundColor Green

Write-Host ""
Write-Host "Copiando archivos de extension..." -ForegroundColor Yellow

try {
    Copy-Item "$TEMP_PGVECTOR\vector.control" -Destination $EXTENSION_DIR -Force -ErrorAction Stop
    Write-Host "  vector.control OK" -ForegroundColor Green
    
    $sqlCount = 0
    Get-ChildItem "$TEMP_PGVECTOR\sql" -Filter "vector--*.sql" | ForEach-Object {
        Copy-Item $_.FullName -Destination $EXTENSION_DIR -Force -ErrorAction Stop
        $sqlCount++
    }
    Write-Host "  $sqlCount archivos SQL OK" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "ERROR: Permiso denegado" -ForegroundColor Red
    Write-Host "SOLUCION: Ejecuta PowerShell como Administrador" -ForegroundColor Yellow
    Write-Host "1. Cierra esta ventana" -ForegroundColor White
    Write-Host "2. Presiona Windows + X" -ForegroundColor White
    Write-Host "3. Selecciona Terminal (Administrador)" -ForegroundColor White
    Write-Host "4. Ejecuta: cd C:\Users\becof\vs\legalwatchpr" -ForegroundColor White
    Write-Host "5. Ejecuta: .\install_pgvector_final.ps1" -ForegroundColor White
    Write-Host ""
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Host ""
Write-Host "Descargando vector.dll..." -ForegroundColor Yellow

$zipPath = "$env:TEMP\pgvector-dll.zip"
$dllUrl = "https://github.com/pgvector/pgvector/releases/download/v0.8.0/pgvector-v0.8.0-pg16-windows-x64.zip"

try {
    Invoke-WebRequest -Uri $dllUrl -OutFile $zipPath -ErrorAction Stop
    Write-Host "  Descargado OK" -ForegroundColor Green
    
    Expand-Archive -Path $zipPath -DestinationPath "$env:TEMP\pgvector-dll" -Force -ErrorAction Stop
    
    $dllFile = Get-ChildItem "$env:TEMP\pgvector-dll" -Recurse -Filter "vector.dll" -ErrorAction Stop | Select-Object -First 1
    
    if ($dllFile) {
        Copy-Item $dllFile.FullName -Destination $LIB_DIR -Force -ErrorAction Stop
        Write-Host "  vector.dll instalado en $LIB_DIR" -ForegroundColor Green
        
        Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
        Remove-Item "$env:TEMP\pgvector-dll" -Recurse -Force -ErrorAction SilentlyContinue
        
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "INSTALACION COMPLETADA CON EXITO" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        
        Write-Host "PROXIMOS PASOS:" -ForegroundColor Cyan
        Write-Host "1. Reinicia PostgreSQL:" -ForegroundColor White
        Write-Host "   Restart-Service postgresql-x64-18" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "2. Verifica la instalacion:" -ForegroundColor White
        Write-Host "   python install_extensions.py" -ForegroundColor Yellow
        Write-Host "   python check_db.py" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "3. Aplica las migraciones:" -ForegroundColor White
        Write-Host "   python manage.py migrate" -ForegroundColor Yellow
        Write-Host ""
        
        Write-Host "Intentando reiniciar PostgreSQL..." -ForegroundColor Yellow
        try {
            Restart-Service postgresql-x64-18 -ErrorAction Stop
            Write-Host "PostgreSQL reiniciado correctamente" -ForegroundColor Green
            Write-Host ""
        } catch {
            Write-Host "No se pudo reiniciar automaticamente" -ForegroundColor Yellow
            Write-Host "Reinicia manualmente desde Services (services.msc)" -ForegroundColor White
            Write-Host ""
        }
        
        exit 0
    } else {
        throw "DLL no encontrado en el archivo ZIP"
    }
} catch {
    Write-Host ""
    Write-Host "ERROR: No se pudo descargar/instalar el DLL automaticamente" -ForegroundColor Yellow
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    
    Write-Host "DESCARGA MANUAL DEL DLL:" -ForegroundColor Cyan
    Write-Host "1. Abre en tu navegador:" -ForegroundColor White
    Write-Host "   https://github.com/pgvector/pgvector/releases/download/v0.8.0/pgvector-v0.8.0-pg16-windows-x64.zip" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "2. Descarga el archivo ZIP" -ForegroundColor White
    Write-Host ""
    Write-Host "3. Extrae vector.dll del ZIP" -ForegroundColor White
    Write-Host ""
    Write-Host "4. Copia vector.dll a:" -ForegroundColor White
    Write-Host "   $LIB_DIR" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "5. Reinicia PostgreSQL:" -ForegroundColor White
    Write-Host "   Restart-Service postgresql-x64-18" -ForegroundColor Yellow
    Write-Host ""
    
    Read-Host "Presiona Enter para salir"
    exit 1
}
