#Requires -Version 5.1
$ErrorActionPreference = 'Stop'
Set-Location 'D:\odoo18-community-chatbot'
$env:TEMP = 'D:\odoo18-community-chatbot\tmp'
$env:TMP  = 'D:\odoo18-community-chatbot\tmp'

Write-Host 'Deteniendo contenedores...' -ForegroundColor Cyan
docker compose down
docker compose ps
