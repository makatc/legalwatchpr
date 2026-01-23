Write-Host '========================================' -ForegroundColor Cyan
Write-Host 'INSTALADOR DE PGVECTOR PARA POSTGRESQL 18' -ForegroundColor Cyan
Write-Host '==========================================' -ForegroundColor Cyan

$TEMP_PGVECTOR = "$env:TEMP\pgvector"
$PG_PATH = "C:\Program Files\PostgreSQL\18"
$EXTENSION_DIR = "$PG_PATH\share\extension"
$LIB_DIR = "$PG_PATH\lib"

if (-not (Test-Path $PG_PATH)) {
    Write-Host 'ERROR: PostgreSQL 18 no encontrado' -ForegroundColor Red
    exit 1
}
Write-Host 'PostgreSQL 18 encontrado' -ForegroundColor Green

if (-not (Test-Path $TEMP_PGVECTOR)) {
    Write-Host 'Clonando pgvector...' -ForegroundColor Yellow
    Set-Location $env:TEMP
    git clone --branch v0.8.0 https://github.com/pgvector/pgvector.git
}

Write-Host 'Copiando archivos...' -ForegroundColor Yellow
try {
    Copy-Item "$TEMP_PGVECTOR\vector.control" -Destination $EXTENSION_DIR -Force
    Write-Host 'vector.control copiado' -ForegroundColor Green
    
    Get-ChildItem "$TEMP_PGVECTOR\sql" -Filter 'vector--*.sql' | ForEach-Object {
        Copy-Item $_.FullName -Destination $EXTENSION_DIR -Force
        Write-Host "Copiado $($_.Name)" -ForegroundColor Green
    }
} catch {
    Write-Host 'ERROR: Ejecuta PowerShell como Administrador' -ForegroundColor Red
    exit 1
}

Write-Host 'Descargando vector.dll...' -ForegroundColor Yellow
$zipPath = "$env:TEMP\pgvector-dll.zip"
$dllUrl = 'https://github.com/pgvector/pgvector/releases/download/v0.8.0/pgvector-v0.8.0-pg16-windows-x64.zip'

try {
    Invoke-WebRequest -Uri $dllUrl -OutFile $zipPath
    Expand-Archive -Path $zipPath -DestinationPath "$env:TEMP\pgvector-dll" -Force
    $dllFile = Get-ChildItem "$env:TEMP\pgvector-dll" -Recurse -Filter 'vector.dll' | Select-Object -First 1
    
    if ($dllFile) {
        Copy-Item $dllFile.FullName -Destination $LIB_DIR -Force
        Write-Host '========================================' -ForegroundColor Green
        Write-Host 'INSTALACION COMPLETADA CON EXITO' -ForegroundColor Green
        Write-Host '========================================' -ForegroundColor Green
        Write-Host 'Ejecuta: python install_extensions.py' -ForegroundColor Cyan
    }
} catch {
    Write-Host 'ERROR al descargar DLL' -ForegroundColor Red
    Write-Host 'Descarga manual: https://github.com/pgvector/pgvector/releases' -ForegroundColor Yellow
}
