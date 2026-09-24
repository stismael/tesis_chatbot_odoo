#Requires -Version 5.1
param(
    [string]$Database = 'odoo18_chatbot'
)
$ErrorActionPreference = 'Stop'
Set-Location 'D:\odoo18-community-chatbot'
$env:TEMP = 'D:\odoo18-community-chatbot\tmp'
$env:TMP  = 'D:\odoo18-community-chatbot\tmp'

& "$PSScriptRoot\check-storage.ps1"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# Cargar variables de entorno
Get-Content '.env' | ForEach-Object {
    if ($_ -match '^\s*([^#=]+)=(.*)$') {
        Set-Item -Path "env:$($matches[1].Trim())" -Value $matches[2].Trim()
    }
}

$backupRoot = 'D:\odoo18-community-chatbot\backups'
if (-not ($backupRoot -match '^[Dd]:\\')) {
    Write-Host 'ERROR: La ruta de respaldo debe estar en D:\' -ForegroundColor Red
    exit 1
}

$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$backupDir = Join-Path $backupRoot "backup_$timestamp"
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

Write-Host "Creando respaldo en: $backupDir" -ForegroundColor Cyan

# 1. PostgreSQL dump (UTF-8, sin BOM; evita corrupción UTF-16 de PowerShell ">")
Write-Host 'Respaldando base de datos PostgreSQL...' -ForegroundColor Gray
$sqlFile = Join-Path $backupDir "${Database}.sql"
$dumpInContainer = "/tmp/${Database}_backup.sql"
docker compose exec -T db sh -c "pg_dump -U `"$env:POSTGRES_USER`" -d `"$Database`" --no-owner --encoding=UTF8 -f `"$dumpInContainer`""
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Error al respaldar PostgreSQL.' -ForegroundColor Red
    exit 1
}
docker compose cp "db:${dumpInContainer}" $sqlFile
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Error al copiar el dump al host.' -ForegroundColor Red
    exit 1
}
docker compose exec -T db rm -f $dumpInContainer | Out-Null

# 2. Filestore Odoo
Write-Host 'Respaldando filestore Odoo...' -ForegroundColor Gray
$filestoreSrc = 'D:\odoo18-community-chatbot\runtime\odoo\filestore'
if (Test-Path $filestoreSrc) {
    $filestoreDst = Join-Path $backupDir 'filestore'
    Copy-Item -Path $filestoreSrc -Destination $filestoreDst -Recurse -Force
}

# 3. Configuración
Write-Host 'Respaldando configuración...' -ForegroundColor Gray
$configDst = Join-Path $backupDir 'config'
New-Item -ItemType Directory -Path $configDst -Force | Out-Null
Copy-Item 'D:\odoo18-community-chatbot\config\odoo.conf' $configDst -Force
Copy-Item 'D:\odoo18-community-chatbot\.env.example' $configDst -Force
# NO copiar .env con contraseñas reales al respaldo por defecto
Copy-Item 'D:\odoo18-community-chatbot\docker-compose.yml' $configDst -Force

# 4. Addons personalizados
Write-Host 'Respaldando addons personalizados...' -ForegroundColor Gray
$addonsDst = Join-Path $backupDir 'addons_custom'
Copy-Item 'D:\odoo18-community-chatbot\addons\custom' $addonsDst -Recurse -Force

# 5. Metadatos
@{
    timestamp   = $timestamp
    database    = $Database
    projectRoot = 'D:\odoo18-community-chatbot'
    createdBy   = 'backup.ps1'
} | ConvertTo-Json | Set-Content (Join-Path $backupDir 'metadata.json') -Encoding UTF8

Write-Host ''
Write-Host "Respaldo completado: $backupDir" -ForegroundColor Green
Get-ChildItem $backupDir -Recurse | Measure-Object -Property Length -Sum | ForEach-Object {
    Write-Host ("Tamaño total: {0:N2} MB" -f ($_.Sum / 1MB)) -ForegroundColor Gray
}
