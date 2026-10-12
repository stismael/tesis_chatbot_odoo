#Requires -Version 5.1
# Ejecuta las pruebas automáticas del módulo chatbot_assistant en una base temporal.
# La base de trabajo (odoo18_chatbot) no se modifica.
param(
    [string]$Database = 'odoo18_chatbot_test'
)
$ErrorActionPreference = 'Stop'
Set-Location 'D:\odoo18-community-chatbot'

$pgUser = 'odoo'
$envLine = Get-Content '.\.env' -ErrorAction SilentlyContinue | Where-Object { $_ -match '^POSTGRES_USER=' }
if ($envLine) { $pgUser = ($envLine -split '=', 2)[1].Trim() }

Write-Host "Recreando base de pruebas '$Database'..." -ForegroundColor Cyan
docker compose exec -T db dropdb -U $pgUser --if-exists $Database
if ($LASTEXITCODE -ne 0) { Write-Host 'No se pudo eliminar la base de pruebas.' -ForegroundColor Red; exit 1 }

Write-Host 'Ejecutando pruebas de chatbot_assistant...' -ForegroundColor Cyan
$log = docker compose exec -T odoo odoo -d $Database -i chatbot_assistant --without-demo=all `
    --test-tags /chatbot_assistant --stop-after-init --no-http --log-level=test 2>&1
$log | Select-String -Pattern 'FAIL:|ERROR:|tests when loading' | ForEach-Object { $_.Line }

$summary = $log | Select-String -Pattern 'tests when loading' | Select-Object -Last 1
if (-not $summary -or $summary.Line -notmatch ' 0 failed, 0 error\(s\)') {
    Write-Host 'Hay pruebas con errores.' -ForegroundColor Red
    exit 1
}
Write-Host 'Todas las pruebas pasaron.' -ForegroundColor Green
