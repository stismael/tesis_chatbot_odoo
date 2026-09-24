#Requires -Version 5.1
param(
    [string]$Database = 'odoo18_chatbot',
    [int]$Limit = 0
)
$ErrorActionPreference = 'Stop'
Set-Location 'D:\odoo18-community-chatbot'

Write-Host "Ejecutando evaluación del chatbot en base '$Database'..." -ForegroundColor Cyan

# Copiar dataset y runner al contenedor vía bind mount de addons no incluye data/
# Montamos temporalmente usando docker cp
docker cp ".\data\eval\eval_dataset.jsonl" "odoo18-chatbot-odoo:/tmp/eval_dataset.jsonl"
docker cp ".\scripts\chatbot_eval_runner.py" "odoo18-chatbot-odoo:/tmp/chatbot_eval_runner.py"

$limitLine = if ($Limit -gt 0) { "summary, rows = run_evaluation(env, '/tmp/eval_dataset.jsonl', limit=$Limit)" } else { "summary, rows = run_evaluation(env, '/tmp/eval_dataset.jsonl')" }

$py = @"
import json
from pathlib import Path
import importlib.util
spec = importlib.util.spec_from_file_location('chatbot_eval_runner', '/tmp/chatbot_eval_runner.py')
mod = importlib.util.module_from_spec(spec)
# Inyectar env antes de exec del bloque final
spec.loader.exec_module(mod)
$limitLine
out_summary = Path('/tmp/eval_summary.json')
out_rows = Path('/tmp/eval_results.jsonl')
out_summary.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
with out_rows.open('w', encoding='utf-8') as fh:
    for row in rows:
        fh.write(json.dumps(row, ensure_ascii=False) + '\n')
print('=== SUMMARY ===')
print(json.dumps(summary, indent=2, ensure_ascii=False))
"@

$py | docker compose exec -T odoo odoo shell -d $Database --no-http
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Error en evaluación.' -ForegroundColor Red
    exit 1
}

New-Item -ItemType Directory -Force -Path '.\data\eval\results' | Out-Null
docker cp "odoo18-chatbot-odoo:/tmp/eval_summary.json" ".\data\eval\results\eval_summary.json"
docker cp "odoo18-chatbot-odoo:/tmp/eval_results.jsonl" ".\data\eval\results\eval_results.jsonl"
Write-Host "Resultados en data\eval\results\" -ForegroundColor Green
Get-Content ".\data\eval\results\eval_summary.json"
