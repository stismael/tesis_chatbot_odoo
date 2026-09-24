#Requires -Version 5.1
param(
    [string]$Service = '',
    [switch]$Follow
)
$ErrorActionPreference = 'Stop'
Set-Location 'D:\odoo18-community-chatbot'

if ($Follow) {
    if ($Service) { docker compose logs -f $Service } else { docker compose logs -f }
} else {
    if ($Service) { docker compose logs --tail 200 $Service } else { docker compose logs --tail 200 }
}
