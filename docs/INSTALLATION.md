# Guía de instalación — Windows desde cero

Esta guía instala WSL2, Docker Desktop y Odoo 18 Community con **todos los datos en D:**.

## Estado detectado en su equipo

| Componente | Estado |
|------------|--------|
| Windows | 10 Home 25H2 (build 26200) |
| PowerShell | 5.1 ✅ |
| Git | 2.39.1 ✅ |
| WSL2 | ❌ No instalado |
| Docker Desktop | ❌ No instalado |
| Espacio C: | ⚠️ ~7 GB libres |
| Espacio D: | ✅ ~446 GB libres |
| Puertos 8069/8072/5432 | ✅ Libres |

> **CRÍTICO:** Con solo ~7 GB en `C:`, debe instalar WSL2 y Docker Desktop en `D:` **antes** de descargar imágenes Docker.

---

## Paso 1: Habilitar WSL2 (requiere administrador)

Abra **PowerShell como Administrador**:

```powershell
# Habilitar características de Windows
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# Reiniciar Windows
Restart-Computer
```

Después del reinicio, en PowerShell como Administrador:

```powershell
wsl --install --no-distribution
wsl --set-default-version 2
```

---

## Paso 2: Instalar Ubuntu en D:\WSL\

**No use** la instalación predeterminada (guarda en C:). Procedimiento:

```powershell
# Crear carpetas en D:
New-Item -ItemType Directory -Force -Path D:\WSL, D:\WSL\backup | Out-Null

# Descargar Ubuntu 24.04
wsl --install -d Ubuntu-24.04 --no-launch
```

Si Ubuntu se instaló en C:, muévalo:

```powershell
wsl --shutdown
wsl --export Ubuntu-24.04 D:\WSL\backup\Ubuntu-24.04.tar
wsl --unregister Ubuntu-24.04
wsl --import Ubuntu-24.04 D:\WSL\Ubuntu-24.04 D:\WSL\backup\Ubuntu-24.04.tar --version 2
```

Verificar:

```powershell
wsl --list --verbose
# Debe mostrar VERSION 2 y BasePath en D:\WSL\
```

Configurar usuario predeterminado:

```powershell
wsl -d Ubuntu-24.04
# Siga las instrucciones para crear usuario/contraseña
```

---

## Paso 3: Instalar Docker Desktop

1. Descargue desde https://www.docker.com/products/docker-desktop/
2. Ejecute el instalador
3. En la instalación, si ofrece **"Use WSL 2 instead of Hyper-V"**, actívelo
4. **Antes de iniciar Docker**, configure almacenamiento en D:

### Configurar Disk image location en D:

1. Inicie Docker Desktop
2. **Settings → Resources → Advanced**
3. **Disk image location:** `D:\DockerData`
4. **Apply & Restart**

Si Docker ya creó datos en C:, mueva primero:

```powershell
wsl --shutdown
# Cierre Docker Desktop completamente (icono bandeja → Quit)
# Luego cambie la ubicación desde Settings
```

Verificar:

```powershell
Get-ChildItem D:\DockerData -Filter *.vhdx -Recurse -Depth 2
docker --version
docker compose version
```

---

## Paso 4: Clonar/preparar el proyecto

El proyecto ya está en:

```text
D:\odoo18-community-chatbot
```

```powershell
Set-Location D:\odoo18-community-chatbot
```

---

## Paso 5: Configurar contraseñas

Edite `.env` y `config\odoo.conf` con contraseñas seguras propias:

```env
POSTGRES_PASSWORD=su_contraseña_segura
ODOO_MASTER_PASSWORD=su_master_password_seguro
```

Ambos archivos deben tener los mismos valores en `POSTGRES_PASSWORD`/`db_password` y `ODOO_MASTER_PASSWORD`/`admin_passwd`.

---

## Paso 6: Verificar almacenamiento

```powershell
.\scripts\check-storage.ps1
```

Debe mostrar todo en verde o solo advertencias menores.

---

## Paso 7: Iniciar Odoo

```powershell
.\scripts\start.ps1
.\scripts\initialize-database.ps1 -Mode clean
```

Espere a que descargue imágenes `postgres:16` y `odoo:18.0` (varios GB en D:).

---

## Paso 8: Acceder y configurar

1. Abra http://localhost:8069
2. Si el asistente web aparece, cree base `odoo18_chatbot` con contraseña de admin
3. Inicie sesión
4. Active modo desarrollador
5. Instale `chatbot_test_data` desde Aplicaciones
6. Genere datos: **Ajustes → Chatbot Test Data → Generar datos de prueba**

---

## Paso 9: Verificar persistencia

```powershell
.\scripts\restart.ps1
# Verifique que la base y datos siguen disponibles
```

---

## Resumen de rutas

| Componente | Ruta |
|------------|------|
| Proyecto | `D:\odoo18-community-chatbot` |
| PostgreSQL data | `D:\odoo18-community-chatbot\runtime\postgres` |
| Filestore Odoo | `D:\odoo18-community-chatbot\runtime\odoo` |
| Logs | `D:\odoo18-community-chatbot\runtime\logs` |
| Docker disk image | `D:\DockerData` |
| WSL Ubuntu | `D:\WSL\Ubuntu-24.04` |
| Respaldos | `D:\odoo18-community-chatbot\backups` |
| Temporales | `D:\odoo18-community-chatbot\tmp` |

---

## Componentes que permanecen en C: (inevitable)

- Ejecutable de Docker Desktop (`C:\Program Files\Docker\`)
- Ejecutable WSL (`C:\Windows\System32\wsl.exe`)
- Caché menor de instaladores
- Perfil de usuario mínimo (`%APPDATA%\Docker\` — solo configuración JSON pequeña)

**No** deben crecer en C: las imágenes Docker, volúmenes ni distribuciones WSL si siguió esta guía.
