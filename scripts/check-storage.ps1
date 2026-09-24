#Requires -Version 5.1
<#
.SYNOPSIS
    Verifica que el proyecto y datos persistentes estén en el disco D:.
.DESCRIPTION
    Detiene el despliegue si detecta rutas importantes en C:.
#>
param(
    [switch]$Strict
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = 'D:\odoo18-community-chatbot'
$issues = @()
$warnings = @()

function Test-OnDriveD {
    param([string]$Path)
    if (-not $Path) { return $false }
    $resolved = [System.IO.Path]::GetFullPath($Path)
    return $resolved -match '^[Dd]:\\'
}

function Add-Issue($msg) { $script:issues += $msg }
function Add-Warning($msg) { $script:warnings += $msg }

Write-Host '=== Verificación de almacenamiento en D: ===' -ForegroundColor Cyan

# Proyecto en D:
$current = (Get-Location).Path
if (-not (Test-OnDriveD $current)) {
    Add-Issue "La carpeta actual NO está en D: ($current). Ejecute: Set-Location D:\odoo18-community-chatbot"
}
if (-not (Test-Path $ProjectRoot)) {
    Add-Issue "No existe la carpeta del proyecto: $ProjectRoot"
} else {
    Write-Host "[OK] Proyecto en D:\odoo18-community-chatbot" -ForegroundColor Green
}

# Espacio en D:
$dDrive = Get-PSDrive D -ErrorAction SilentlyContinue
if ($dDrive) {
    $freeGb = [math]::Round($dDrive.Free / 1GB, 2)
    Write-Host "[INFO] Espacio libre en D: ${freeGb} GB" -ForegroundColor Gray
    if ($freeGb -lt 20) {
        Add-Warning "Espacio libre en D: bajo (${freeGb} GB). Se recomiendan al menos 20 GB."
    }
} else {
    Add-Issue 'No se encontró la unidad D:'
}

# Carpetas runtime
$runtimePaths = @(
    "$ProjectRoot\runtime\postgres",
    "$ProjectRoot\runtime\odoo",
    "$ProjectRoot\runtime\logs",
    "$ProjectRoot\backups",
    "$ProjectRoot\tmp"
)
foreach ($p in $runtimePaths) {
    if (-not (Test-OnDriveD $p)) {
        Add-Issue "Ruta runtime fuera de D: $p"
    } elseif (-not (Test-Path $p)) {
        Add-Warning "Carpeta no existe aún (se creará al iniciar): $p"
    } else {
        Write-Host "[OK] $p" -ForegroundColor Green
    }
}

# .env en D: y sin rutas C:
$envFile = Join-Path $ProjectRoot '.env'
if (Test-Path $envFile) {
    $envContent = Get-Content $envFile -Raw
    if ($envContent -match '[Cc]:[/\\]') {
        Add-Issue 'El archivo .env contiene rutas en C:. Corrija las variables PROJECT_ROOT, *_PATH.'
    } else {
        Write-Host '[OK] .env sin rutas C:' -ForegroundColor Green
    }
}

# Docker Compose bind mounts
$composeFile = Join-Path $ProjectRoot 'docker-compose.yml'
if (Test-Path $composeFile) {
    $compose = Get-Content $composeFile -Raw
    if ($compose -match '[Cc]:[/\\]') {
        Add-Issue 'docker-compose.yml contiene rutas absolutas en C:'
    }
    if ($compose -match '\./runtime/') {
        Write-Host '[OK] docker-compose.yml usa bind mounts relativos en D:' -ForegroundColor Green
    }
}

# Docker Desktop disk image location
$dockerSettings = @(
    "$env:APPDATA\Docker\settings-store.json",
    "$env:APPDATA\Docker\settings.json"
)
$dockerDiskFound = $false
foreach ($sf in $dockerSettings) {
    if (Test-Path $sf) {
        try {
            $json = Get-Content $sf -Raw | ConvertFrom-Json
            $diskPath = $json.diskPath
            if (-not $diskPath) { $diskPath = $json.'disk-image-location' }
            if ($diskPath) {
                $dockerDiskFound = $true
                if (Test-OnDriveD $diskPath) {
                    Write-Host "[OK] Docker Desktop disk image: $diskPath" -ForegroundColor Green
                } else {
                    Add-Warning "Docker Desktop disk image en C: u otra unidad: $diskPath. Mueva a D:\DockerData."
                }
            }
        } catch {
            Add-Warning "No se pudo leer configuración Docker: $sf"
        }
    }
}
if (-not $dockerDiskFound) {
    $vhdxOnD = Get-ChildItem 'D:\DockerData','D:\Docker' -Filter '*.vhdx' -Recurse -Depth 3 -ErrorAction SilentlyContinue
    if ($vhdxOnD) {
        Write-Host '[OK] Imágenes WSL/Docker detectadas en D:' -ForegroundColor Green
        $vhdxOnD | ForEach-Object { Write-Host "  $($_.FullName)" -ForegroundColor Gray }
    } else {
        Add-Warning 'No se pudo determinar ubicación de Docker Desktop. Configure Disk image location en D:\DockerData.'
    }
}

# WSL distribuciones
try {
    $wslList = wsl --list --verbose 2>&1
    if ($LASTEXITCODE -eq 0 -and $wslList -notmatch 'no está instalado') {
        Write-Host '[INFO] Distribuciones WSL:' -ForegroundColor Gray
        Write-Host $wslList
        $lxss = Get-ChildItem 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss' -ErrorAction SilentlyContinue
        foreach ($key in $lxss) {
            $props = Get-ItemProperty $key.PSPath
            $base = $props.BasePath
            $name = $props.DistributionName
            if (Test-OnDriveD $base) {
                Write-Host "[OK] WSL $name en D: ($base)" -ForegroundColor Green
            } else {
                Add-Warning "WSL $name NO está en D: ($base). Considere exportar/importar a D:\WSL\"
            }
        }
    } else {
        Add-Warning 'WSL2 no instalado o no disponible. Requerido para Docker Desktop en Windows.'
    }
} catch {
    Add-Warning 'WSL2 no instalado. Instale con: wsl --install (ver docs/STORAGE_ON_D.md)'
}

# Advertencia espacio C:
$cDrive = Get-PSDrive C -ErrorAction SilentlyContinue
if ($cDrive) {
    $cFree = [math]::Round($cDrive.Free / 1GB, 2)
    if ($cFree -lt 15) {
        Add-Warning "ADVERTENCIA: Solo ${cFree} GB libres en C:. Instale WSL/Docker en D: antes de continuar."
    }
}

Write-Host ''
if ($warnings.Count -gt 0) {
    Write-Host '=== Advertencias ===' -ForegroundColor Yellow
    $warnings | ForEach-Object { Write-Host "  [!] $_" -ForegroundColor Yellow }
}

if ($issues.Count -gt 0) {
    Write-Host '=== ERRORES BLOQUEANTES ===' -ForegroundColor Red
    $issues | ForEach-Object { Write-Host "  [X] $_" -ForegroundColor Red }
    Write-Host ''
    Write-Host 'Despliegue DETENIDO. Corrija las rutas antes de continuar.' -ForegroundColor Red
    exit 1
}

Write-Host '=== Verificación completada: almacenamiento en D: OK ===' -ForegroundColor Green
exit 0
