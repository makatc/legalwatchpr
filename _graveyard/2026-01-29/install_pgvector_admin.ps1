# Instalar pgvector para PostgreSQL 18 - Requiere permisos de administrador

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "INSTALADOR DE PGVECTOR PARA POSTGRESQL 18" -ForegroundColor Cyan
Write-Host "==========================================`n" -ForegroundColor Cyan

$TEMP_PGVECTOR = "$env:TEMP\pgvector"
$PG_PATH = "C:\Program Files\PostgreSQL\18"
$EXTENSION_DIR = "$PG_PATH\share\extension"
$LIB_DIR = "$PG_PATH\lib"

# Verificar PostgreSQL
if (-not (Test-Path $PG_PATH)) {
    Write-Host "❌ ERROR: PostgreSQL 18 no encontrado en $PG_PATH" -ForegroundColor Red
    exit 1
}
Write-Host "✅ PostgreSQL 18 encontrado" -ForegroundColor Green

# Verificar código fuente pgvector
if (-not (Test-Path $TEMP_PGVECTOR)) {
    Write-Host "❌ ERROR: Código fuente de pgvector no encontrado" -ForegroundColor Red
    Write-Host "Clonando repositorio de pgvector..." -ForegroundColor Yellow
    Set-Location $env:TEMP
    git clone --branch v0.8.0 https://github.com/pgvector/pgvector.git
}
Write-Host "✅ Código fuente de pgvector disponible" -ForegroundColor Green

# Copiar archivos de extensión
Write-Host "`nCopiando archivos de extensión..." -ForegroundColor Yellow

try {
    Copy-Item "$TEMP_PGVECTOR\vector.control" -Destination $EXTENSION_DIR -Force -ErrorAction Stop
    Write-Host "✅ vector.control copiado" -ForegroundColor Green
    
    $sqlFiles = Get-ChildItem "$TEMP_PGVECTOR\sql" -Filter "vector--*.sql"
    foreach ($file in $sqlFiles) {
        Copy-Item $file.FullName -Destination $EXTENSION_DIR -Force -ErrorAction Stop
        Write-Host "✅ $($file.Name) copiado" -ForegroundColor Green
    }
}
catch {
    Write-Host "❌ ERROR: Permiso denegado. Ejecuta PowerShell como Administrador." -ForegroundColor Red
    Write-Host "Haz clic derecho en PowerShell > Ejecutar como administrador" -ForegroundColor Yellow
    Write-Host "Luego ejecuta: cd '$PWD'; .\install_pgvector_admin.ps1" -ForegroundColor White
    exit 1
}

Write-Host "`n⚠️  NOTA: Se copiaron los archivos SQL pero falta el archivo DLL" -ForegroundColor Yellow
Write-Host "pgvector requiere compilar vector.dll con Visual Studio`n" -ForegroundColor Yellow

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SIGUIENTE PASO: COMPILAR vector.dll" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "OPCIÓN MÁS SIMPLE: Descargar DLL precompilado`n" -ForegroundColor Yellow

# Intentar descargar DLL precompilado
$dllUrl = "https://github.com/pgvector/pgvector/releases/download/v0.8.0/pgvector-v0.8.0-pg16-windows-x64.zip"
Write-Host "Intentando descargar DLL para PG16 (compatible con PG18)..." -ForegroundColor Yellow

try {
    $zipPath = "$env:TEMP\pgvector-dll.zip"
    Invoke-WebRequest -Uri $dllUrl -OutFile $zipPath -ErrorAction Stop
    
    # Extraer ZIP
    Expand-Archive -Path $zipPath -DestinationPath "$env:TEMP\pgvector-dll" -Force
    
    # Copiar DLL
    $dllFile = Get-ChildItem "$env:TEMP\pgvector-dll" -Recurse -Filter "vector.dll" | Select-Object -First 1
    if ($dllFile) {
        Copy-Item $dllFile.FullName -Destination $LIB_DIR -Force -ErrorAction Stop
        Write-Host "✅ vector.dll instalado correctamente!" -ForegroundColor Green
        
        Write-Host "`n========================================" -ForegroundColor Green
        Write-Host "INSTALACIÓN COMPLETADA CON ÉXITO" -ForegroundColor Green
        Write-Host "========================================`n" -ForegroundColor Green
        
        Write-Host "Ahora ejecuta en tu proyecto:" -ForegroundColor Cyan
        Write-Host "  python install_extensions.py" -ForegroundColor White
        Write-Host "  python manage.py migrate`n" -ForegroundColor White
        
        exit 0
    }
}
catch {
    Write-Host "⚠️  No se pudo descargar DLL automáticamente" -ForegroundColor Yellow
}

Write-Host "`nDESCARGA MANUAL DEL DLL:" -ForegroundColor Cyan
Write-Host "1. Ve a: https://github.com/pgvector/pgvector/releases" -ForegroundColor White
Write-Host "2. Descarga: pgvector-vX.X.X-pg16-windows-x64.zip (o similar)" -ForegroundColor White
Write-Host "3. Extrae vector.dll y cópialo a: $LIB_DIR" -ForegroundColor White
Write-Host "4. Reinicia el servicio de PostgreSQL`n" -ForegroundColor White

Write-Host "O ejecuta este comando para reintentar descarga:" -ForegroundColor Yellow
Write-Host "  .\download_pgvector_dll.ps1`n" -ForegroundColor White
