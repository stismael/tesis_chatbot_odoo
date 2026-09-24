#Requires -Version 5.1
param(
    [Parameter(Mandatory = $true)]
    [string]$ModuleName,
    [string]$Database = 'odoo18_chatbot'
)
$ErrorActionPreference = 'Stop'
Set-Location 'D:\odoo18-community-chatbot'
$env:TEMP = 'D:\odoo18-community-chatbot\tmp'
$env:TMP  = 'D:\odoo18-community-chatbot\tmp'

& "$PSScriptRoot\check-storage.ps1"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Actualizando módulo '$ModuleName' en base '$Database'..." -ForegroundColor Cyan
docker compose exec -T odoo odoo -d $Database -u $ModuleName --stop-after-init
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Error al actualizar módulo.' -ForegroundColor Red
    exit 1
}
Write-Host 'Módulo actualizado correctamente.' -ForegroundColor Green
