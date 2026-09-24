#Requires -Version 5.1
$ErrorActionPreference = 'Stop'
Set-Location 'D:\odoo18-community-chatbot'
$env:TEMP = 'D:\odoo18-community-chatbot\tmp'
$env:TMP  = 'D:\odoo18-community-chatbot\tmp'

& "$PSScriptRoot\check-storage.ps1"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$PSScriptRoot\sync-config.ps1"

Write-Host 'Iniciando contenedores Odoo 18...' -ForegroundColor Cyan
docker compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Error al iniciar contenedores. Verifique que Docker Desktop esté ejecutándose.' -ForegroundColor Red
    exit 1
}
docker compose ps
Write-Host ''
Write-Host 'Odoo disponible en: http://localhost:8069' -ForegroundColor Green
