#Requires -Version 5.1
param(
    [Parameter(Mandatory = $true)]
    [string]$BackupPath,
    [string]$Database = 'odoo18_chatbot',
    [switch]$Force
)
$ErrorActionPreference = 'Stop'
Set-Location 'D:\odoo18-community-chatbot'
$env:TEMP = 'D:\odoo18-community-chatbot\tmp'
$env:TMP  = 'D:\odoo18-community-chatbot\tmp'

& "$PSScriptRoot\check-storage.ps1"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$resolved = [System.IO.Path]::GetFullPath($BackupPath)
if (-not (Test-Path $resolved)) {
    Write-Host "ERROR: No existe el respaldo: $resolved" -ForegroundColor Red
    exit 1
}
if ($resolved -notmatch '^[Dd]:\\') {
    Write-Host 'ERROR: El respaldo debe estar en D:\' -ForegroundColor Red
    exit 1
}

Get-Content '.env' | ForEach-Object {
    if ($_ -match '^\s*([^#=]+)=(.*)$') {
        Set-Item -Path "env:$($matches[1].Trim())" -Value $matches[2].Trim()
    }
}

# Verificar si la base existe
$dbExists = docker compose exec -T db psql -U $env:POSTGRES_USER -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$Database'" 2>$null
if ($dbExists -match '1' -and -not $Force) {
    Write-Host "ADVERTENCIA: La base '$Database' ya existe y será SOBRESCRITA." -ForegroundColor Yellow
    $confirm = Read-Host 'Escriba SI para continuar'
    if ($confirm -ne 'SI') {
        Write-Host 'Restauración cancelada.' -ForegroundColor Yellow
        exit 0
    }
}

Write-Host 'Deteniendo Odoo...' -ForegroundColor Cyan
docker compose stop odoo

# Restaurar PostgreSQL
$sqlPlain = Join-Path $resolved "${Database}.sql"
$sqlGz = Join-Path $resolved "${Database}.sql.gz"

if (Test-Path $sqlPlain) {
    Write-Host 'Restaurando base de datos...' -ForegroundColor Gray
    if ($dbExists -match '1') {
        docker compose exec -T db dropdb -U $env:POSTGRES_USER --if-exists $Database
    }
    docker compose exec -T db createdb -U $env:POSTGRES_USER -O $env:POSTGRES_USER $Database
    Get-Content $sqlPlain -Raw | docker compose exec -T db psql -U $env:POSTGRES_USER -d $Database -q
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'Error al restaurar SQL.' -ForegroundColor Red
        exit 1
    }
} elseif (Test-Path $sqlGz) {
    Write-Host 'Restaurando base de datos comprimida (vía contenedor)...' -ForegroundColor Gray
    if ($dbExists -match '1') {
        docker compose exec -T db dropdb -U $env:POSTGRES_USER --if-exists $Database
    }
    docker compose exec -T db createdb -U $env:POSTGRES_USER -O $env:POSTGRES_USER $Database
    docker compose exec -T db bash -c "gunzip -c '/backups/$([System.IO.Path]::GetFileName($resolved))/${Database}.sql.gz' | psql -U $env:POSTGRES_USER -d $Database -q"
} else {
    Write-Host 'ERROR: No se encontró archivo SQL en el respaldo.' -ForegroundColor Red
    exit 1
}

# Restaurar filestore
$filestoreBackup = Join-Path $resolved 'filestore'
$filestoreTarget = 'D:\odoo18-community-chatbot\runtime\odoo\filestore'
if (Test-Path $filestoreBackup) {
    Write-Host 'Restaurando filestore...' -ForegroundColor Gray
    if (Test-Path $filestoreTarget) {
        Remove-Item $filestoreTarget -Recurse -Force
    }
    Copy-Item $filestoreBackup $filestoreTarget -Recurse -Force
}

# Restaurar addons si existen en respaldo
$addonsBackup = Join-Path $resolved 'addons_custom'
if (Test-Path $addonsBackup) {
    Write-Host 'Restaurando addons personalizados...' -ForegroundColor Gray
    Copy-Item "$addonsBackup\*" 'D:\odoo18-community-chatbot\addons\custom' -Recurse -Force
}

Write-Host 'Reiniciando Odoo...' -ForegroundColor Cyan
docker compose start odoo
Start-Sleep -Seconds 10
docker compose ps

Write-Host ''
Write-Host 'Restauración completada. Verifique en http://localhost:8069' -ForegroundColor Green
