# Script para sincronizar contraseñas de .env a config/odoo.conf
$ErrorActionPreference = 'Stop'
Set-Location 'D:\odoo18-community-chatbot'

$envVars = @{}
Get-Content '.env' | ForEach-Object {
    if ($_ -match '^\s*([^#=]+)=(.*)$') {
        $envVars[$matches[1].Trim()] = $matches[2].Trim()
    }
}

$template = @'
[options]
admin_passwd = CAMBIAR_MASTER_PASSWORD
db_host = db
db_port = 5432
db_user = odoo
db_password = CAMBIAR_CONTRASENA_POSTGRES
addons_path = /mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons
data_dir = /var/lib/odoo
proxy_mode = False
list_db = True
log_level = info
logfile = /var/log/odoo/odoo.log
workers = 0
max_cron_threads = 1
'@

$conf = $template
$conf = $conf -replace 'CAMBIAR_MASTER_PASSWORD', $envVars['ODOO_MASTER_PASSWORD']
$conf = $conf -replace 'CAMBIAR_CONTRASENA_POSTGRES', $envVars['POSTGRES_PASSWORD']

# UTF-8 sin BOM (requerido por Odoo en Linux)
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText((Join-Path (Get-Location) 'config\odoo.conf'), $conf, $utf8NoBom)
Write-Host 'config/odoo.conf sincronizado desde .env (UTF-8 sin BOM)' -ForegroundColor Green
