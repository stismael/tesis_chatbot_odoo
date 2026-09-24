#Requires -Version 5.1
param(
    [ValidateSet('demo', 'clean', 'none')]
    [string]$Mode = 'clean',
    [switch]$SkipModuleInstall,
    [switch]$GenerateSyntheticData
)
$ErrorActionPreference = 'Stop'
Set-Location 'D:\odoo18-community-chatbot'
$env:TEMP = 'D:\odoo18-community-chatbot\tmp'
$env:TMP  = 'D:\odoo18-community-chatbot\tmp'

function Write-Step($msg) { Write-Host "`n>> $msg" -ForegroundColor Cyan }

Write-Step '1. Verificando almacenamiento en D:'
& "$PSScriptRoot\check-storage.ps1"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$PSScriptRoot\sync-config.ps1"

Write-Step '2. Verificando Docker Desktop'
try {
    $dockerVersion = docker --version 2>&1
    Write-Host $dockerVersion -ForegroundColor Gray
} catch {
    Write-Host 'ERROR: Docker no está instalado o no está en PATH.' -ForegroundColor Red
    Write-Host 'Instale Docker Desktop y configure almacenamiento en D:\DockerData (ver docs/INSTALLATION.md)' -ForegroundColor Yellow
    exit 1
}

docker info *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host 'ERROR: Docker Desktop no está ejecutándose. Inícielo y reintente.' -ForegroundColor Red
    exit 1
}

Write-Step '3. Cargando variables de entorno'
Get-Content '.env' | ForEach-Object {
    if ($_ -match '^\s*([^#=]+)=(.*)$') {
        Set-Item -Path "env:$($matches[1].Trim())" -Value $matches[2].Trim()
    }
}
$dbName = $env:ODOO_DATABASE
if (-not $dbName) { $dbName = 'odoo18_chatbot' }

Write-Step '4. Iniciando PostgreSQL'
docker compose up -d db
$maxWait = 60
$waited = 0
while ($waited -lt $maxWait) {
    $health = docker inspect --format='{{.State.Health.Status}}' odoo18-chatbot-db 2>$null
    if ($health -eq 'healthy') { break }
    Start-Sleep -Seconds 3
    $waited += 3
    Write-Host "  Esperando PostgreSQL... ($waited s)" -ForegroundColor Gray
}
if ($health -ne 'healthy') {
    Write-Host 'ERROR: PostgreSQL no alcanzó estado healthy.' -ForegroundColor Red
    docker compose logs db
    exit 1
}
Write-Host 'PostgreSQL saludable.' -ForegroundColor Green

Write-Step '5. Iniciando Odoo'
docker compose up -d odoo
Start-Sleep -Seconds 15

Write-Step '6. Verificando HTTP en http://localhost:8069'
try {
    $response = Invoke-WebRequest -Uri 'http://localhost:8069' -UseBasicParsing -TimeoutSec 30
    Write-Host "HTTP $($response.StatusCode) - Odoo responde." -ForegroundColor Green
} catch {
    Write-Host 'ADVERTENCIA: Odoo aún no responde. Revise logs con .\scripts\logs.ps1 -Follow' -ForegroundColor Yellow
}

Write-Step '7. Verificando si la base ya existe'
$dbExists = docker compose exec -T db psql -U $env:POSTGRES_USER -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$dbName'" 2>$null

if ($dbExists -match '1') {
    Write-Host "La base '$dbName' ya existe. Omitiendo creación." -ForegroundColor Yellow
} else {
    Write-Step "8. Creando base '$dbName'"
    $modules = 'base,contacts,product,sale_management,stock,account'
    $demoFlag = if ($Mode -eq 'demo') { '' } else { '--without-demo=all' }

    if ($Mode -eq 'demo') {
        Write-Host 'Modo DEMO: se cargarán datos demostrativos de Odoo.' -ForegroundColor Yellow
        docker compose stop odoo
        docker compose run --rm odoo odoo -d $dbName -i $modules --stop-after-init --db_host=db --db_user=$env:POSTGRES_USER --db_password=$env:POSTGRES_PASSWORD
    } else {
        Write-Host 'Modo LIMPIO: sin datos demo de Odoo.' -ForegroundColor Yellow
        docker compose stop odoo
        docker compose run --rm odoo odoo -d $dbName -i $modules --without-demo=all --stop-after-init --db_host=db --db_user=$env:POSTGRES_USER --db_password=$env:POSTGRES_PASSWORD
    }

    if ($LASTEXITCODE -ne 0) {
        Write-Host 'ERROR al crear la base. Revise logs.' -ForegroundColor Red
        exit 1
    }
    docker compose up -d odoo
    Write-Host "Base '$dbName' creada con módulos: $modules" -ForegroundColor Green
}

if (-not $SkipModuleInstall) {
    Write-Step '9. Instalando módulos chatbot_test_data y chatbot_assistant'
    docker compose exec -T odoo odoo -d $dbName -i chatbot_test_data,chatbot_assistant --stop-after-init
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'ADVERTENCIA: Error al instalar módulos personalizados.' -ForegroundColor Yellow
    }
}

if ($GenerateSyntheticData) {
    Write-Step '10. Actualizando módulo y generando datos realistas'
    docker compose exec -T odoo odoo -d $dbName -u chatbot_test_data --stop-after-init
    docker compose up -d odoo
    Start-Sleep -Seconds 8
    Get-Content "$PSScriptRoot\generate_synthetic_data.py" | docker compose exec -T odoo odoo shell -d $dbName --no-http
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'ERROR al generar datos sintéticos.' -ForegroundColor Red
        exit 1
    }
    Write-Host 'Datos realistas generados correctamente.' -ForegroundColor Green
}

Write-Host ''
Write-Host '=== INICIALIZACIÓN COMPLETADA ===' -ForegroundColor Green
Write-Host "URL:      http://localhost:8069"
Write-Host "Base:     $dbName"
Write-Host "Usuario:  admin (contraseña definida al crear la base en el asistente web)"
Write-Host "Master:   Ver ODOO_MASTER_PASSWORD en .env"
Write-Host ''
Write-Host 'Próximos pasos:'
Write-Host '  1. Abra http://localhost:8069 e inicie sesión'
Write-Host '  2. Active modo desarrollador (Ajustes > Activar modo desarrollador)'
Write-Host '  3. Para datos sintéticos: Apps > chatbot_test_data > Generar datos de prueba'
Write-Host '  4. Configure la API del LLM: Chatbot > Ajustes'
Write-Host '  5. Consulte data/EXPECTED_RESULTS.md y docs/CHATBOT_ASSISTANT.md'
