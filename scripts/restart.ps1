#Requires -Version 5.1
$ErrorActionPreference = 'Stop'
Set-Location 'D:\odoo18-community-chatbot'
$env:TEMP = 'D:\odoo18-community-chatbot\tmp'
$env:TMP  = 'D:\odoo18-community-chatbot\tmp'

& "$PSScriptRoot\stop.ps1"
Start-Sleep -Seconds 3
& "$PSScriptRoot\start.ps1"
