# Odoo 18 Community — Chatbot Test Environment

Entorno de desarrollo local de **Odoo 18 Community** con PostgreSQL 16 en Docker, optimizado para almacenar **todos los datos persistentes en el disco D:**.

## Arquitectura

```text
Windows 11/10 + Docker Desktop (WSL2 backend en D:)
└── D:\odoo18-community-chatbot\
    ├── docker-compose.yml
    ├── config\odoo.conf
    ├── addons\custom\          ← módulos personalizados (chatbot_test_data)
    ├── runtime\
    │   ├── postgres\           ← datos PostgreSQL (bind mount)
    │   ├── odoo\               ← filestore Odoo (bind mount)
    │   └── logs\               ← logs Odoo
    └── backups\                ← respaldos
```

| Servicio | Imagen | Puerto | Red |
|----------|--------|--------|-----|
| PostgreSQL 16 | `postgres:16` | interno 5432 | `odoo_internal` |
| Odoo 18 Community | `odoo:18.0` | 8069, 8072 | `odoo_internal` |

## Requisitos previos

- Windows 10/11 (64 bits)
- **Disco D:** con ≥ 20 GB libres
- PowerShell 5.1+
- Git
- **WSL2** (backend de Docker Desktop)
- **Docker Desktop** con almacenamiento en `D:\DockerData`
- Puertos libres: 8069, 8072

> **ADVERTENCIA:** En su sistema, `C:` tiene espacio muy limitado (~7 GB). Instale WSL2 y Docker Desktop directamente en `D:` siguiendo `docs/STORAGE_ON_D.md`.

## Inicio rápido

```powershell
Set-Location D:\odoo18-community-chatbot

# 1. Verificar almacenamiento
.\scripts\check-storage.ps1

# 2. Iniciar servicios
.\scripts\start.ps1

# 3. Inicializar base (limpia, sin demo Odoo)
.\scripts\initialize-database.ps1 -Mode clean

# 4. Abrir navegador
start http://localhost:8069
```

## Variables de entorno

Copie `.env.example` a `.env` si aún no existe. **Cambie obligatoriamente:**

| Variable | Descripción |
|----------|-------------|
| `POSTGRES_PASSWORD` | Contraseña del usuario PostgreSQL `odoo` |
| `ODOO_MASTER_PASSWORD` | Contraseña maestra de administración de bases |

Las contraseñas en `.env` deben coincidir con `config/odoo.conf` (`db_password` y `admin_passwd`). En este equipo, `.\scripts\start.ps1` genera `odoo.conf` desde `.env` (no suba `odoo.conf` a Git).

> `.env` y `config/odoo.conf` están en `.gitignore` — nunca los suba a Git. La API key de Gemini/Groq se configura en Odoo (**Chatbot → Ajustes**), no en archivos del repositorio.

## Clonar desde GitHub

```powershell
git clone git@github.com:stismael/tesis_chatbot_odoo.git
Set-Location tesis_chatbot_odoo
Copy-Item .env.example .env
# Edite POSTGRES_PASSWORD y ODOO_MASTER_PASSWORD en .env
.\scripts\start.ps1
```

## Scripts PowerShell

| Script | Uso |
|--------|-----|
| `check-storage.ps1` | Verifica que todo esté en D: |
| `start.ps1` | `docker compose up -d` |
| `stop.ps1` | `docker compose down` |
| `restart.ps1` | Reinicia contenedores |
| `logs.ps1` | Ver logs (`-Follow` para seguimiento) |
| `initialize-database.ps1` | Crea base e instala módulos |
| `update-module.ps1` | Actualiza módulo personalizado |
| `backup.ps1` | Respaldo completo en `backups\` |
| `restore.ps1` | Restaura desde respaldo |

### Ejemplos

```powershell
.\scripts\logs.ps1 -Service odoo -Follow
.\scripts\update-module.ps1 chatbot_test_data
.\scripts\backup.ps1
.\scripts\restore.ps1 -BackupPath D:\odoo18-community-chatbot\backups\backup_20260711_120000
```

## Creación de base de datos

### Opción 1: Con datos demo de Odoo

```powershell
.\scripts\initialize-database.ps1 -Mode demo
```

Carga los datos demostrativos estándar de Odoo (empresa ficticia, productos, etc.).

### Opción 2: Base limpia (recomendada para tesis)

```powershell
.\scripts\initialize-database.ps1 -Mode clean
```

Sin datos demo de Odoo. Use después el módulo `chatbot_test_data` para datos controlados.

### Asistente web

1. Abra http://localhost:8069
2. Cree base `odoo18_chatbot`
3. Instale módulos: Ventas, Inventario, Facturación, Contactos, Productos

## Módulos instalados

| Módulo técnico | Aplicación |
|----------------|------------|
| `base` | Base |
| `contacts` | Contactos |
| `product` | Productos |
| `sale_management` | Ventas |
| `stock` | Inventario |
| `account` | Facturación |
| `chatbot_test_data` | Datos sintéticos (personalizado) |
| `chatbot_assistant` | Asistente conversacional (personalizado) |

## Asistente conversacional (chatbot_assistant)

1. Instale/actualice: `.\scripts\update-module.ps1 -ModuleName chatbot_assistant`
2. Configure API key en **Chatbot → Ajustes** (Gemini Flash recomendado)
3. Use **Chatbot → Nueva consulta**
4. Evaluación Cap. 5: `.\scripts\run-chatbot-eval.ps1`

Guía completa: [docs/CHATBOT_ASSISTANT.md](docs/CHATBOT_ASSISTANT.md).

## Modo desarrollador

1. Inicie sesión como administrador
2. **Ajustes → Activar modo desarrollador**
3. Edite módulos en `D:\odoo18-community-chatbot\addons\custom\`
4. Actualice con: `.\scripts\update-module.ps1 <nombre_modulo>`

## Datos sintéticos (chatbot_test_data)

1. Instale el módulo desde **Aplicaciones** (actualizar lista si no aparece)
2. Vaya a **Ajustes → Chatbot Test Data → Generar datos de prueba**
3. Confirme y ejecute

O por línea de comandos:

```powershell
Get-Content .\scripts\generate_synthetic_data.py | docker compose exec -T odoo odoo shell -d odoo18_chatbot --no-http
```

Verifique casos ancla en `data/EXPECTED_RESULTS.md`.

## Importación CSV

Plantillas en `data/csv/`:

- `clientes.csv` — Contactos
- `productos.csv` — Productos
- `inventario.csv` — Documentación de ajustes de inventario

Importe desde **Favoritos → Importar registros** en cada vista.

## Respaldo y restauración

```powershell
# Respaldo
.\scripts\backup.ps1

# Restauración (pide confirmación si la base existe)
.\scripts\restore.ps1 -BackupPath D:\odoo18-community-chatbot\backups\backup_YYYYMMDD_HHMMSS
```

## Comandos Docker equivalentes

```powershell
Set-Location D:\odoo18-community-chatbot
docker compose config
docker compose up -d
docker compose ps
docker compose logs db
docker compose logs odoo
docker compose exec db pg_isready -U odoo
docker compose down
```

## Solución de problemas

| Problema | Solución |
|----------|----------|
| Docker no reconocido | Instale Docker Desktop, reinicie PowerShell |
| PostgreSQL unhealthy | Revise `runtime\postgres`, elimine `postmaster.pid` si existe |
| Permisos en bind mount | Verifique que Docker disk image esté en D: |
| Odoo no carga módulo | `.\scripts\update-module.ps1 chatbot_test_data` |
| Puerto 8069 ocupado | Cambie `ODOO_PORT` en `.env` |
| Espacio en C: bajo | Mueva Docker/WSL a D: (ver `docs/STORAGE_ON_D.md`) |

## Documentación adicional

- [Guía de instalación desde cero](docs/INSTALLATION.md)
- [Almacenamiento en disco D:](docs/STORAGE_ON_D.md)
- [Asistente conversacional](docs/CHATBOT_ASSISTANT.md)
- [Resultados esperados del generador](data/EXPECTED_RESULTS.md)

## Licencia

Odoo Community Edition — LGPL-3. Módulos `chatbot_test_data` y `chatbot_assistant` — LGPL-3.
