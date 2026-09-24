#Requires -Version 5.1
<#
.SYNOPSIS
    Elimina la base actual, limpia filestore y recrea con datos realistas.
#>
param(
    [string]$Database = 'odoo18_chatbot',
    [switch]$SkipSyntheticData
)
$ErrorActionPreference = 'Stop'
Set-Location 'D:\odoo18-community-chatbot'
$env:TEMP = 'D:\odoo18-community-chatbot\tmp'
$env:TMP  = 'D:\odoo18-community-chatbot\tmp'

& "$PSScriptRoot\check-storage.ps1"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Get-Content '.env' | ForEach-Object {
    if ($_ -match '^\s*([^#=]+)=(.*)$') {
        Set-Item -Path "env:$($matches[1].Trim())" -Value $matches[2].Trim()
    }
}
if (-not $Database) { $Database = $env:ODOO_DATABASE }
if (-not $Database) { $Database = 'odoo18_chatbot' }

Write-Host "=== RESETEO DE BASE: $Database ===" -ForegroundColor Yellow
Write-Host 'Se eliminará la base, el filestore y se recreará con datos realistas.' -ForegroundColor Yellow
$confirm = Read-Host 'Escriba SI para continuar'
if ($confirm -ne 'SI') {
    Write-Host 'Operación cancelada.' -ForegroundColor Yellow
    exit 0
}

Write-Host 'Deteniendo Odoo...' -ForegroundColor Cyan
docker compose stop odoo

$dbExists = docker compose exec -T db psql -U $env:POSTGRES_USER -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$Database'" 2>$null
if ($dbExists -match '1') {
    Write-Host "Eliminando base $Database..." -ForegroundColor Cyan
    docker compose exec -T db psql -U $env:POSTGRES_USER -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$Database' AND pid <> pg_backend_pid();"
    docker compose exec -T db dropdb -U $env:POSTGRES_USER --if-exists $Database
}

$filestorePath = Join-Path (Get-Location) "runtime\odoo\filestore\$Database"
if (Test-Path $filestorePath) {
    Write-Host "Eliminando filestore: $filestorePath" -ForegroundColor Cyan
    Remove-Item $filestorePath -Recurse -Force
}

$sessionsPath = Join-Path (Get-Location) "runtime\odoo\sessions"
if (Test-Path $sessionsPath) {
    Remove-Item "$sessionsPath\*" -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host 'Recreando base e instalando módulos...' -ForegroundColor Cyan
& "$PSScriptRoot\initialize-database.ps1" -Mode clean -GenerateSyntheticData

if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ''
Write-Host '=== BASE RECREADA CON DATOS REALISTAS ===' -ForegroundColor Green
Write-Host "URL:  http://localhost:8069"
Write-Host "Base: $Database"
Write-Host 'Usuario: admin'
