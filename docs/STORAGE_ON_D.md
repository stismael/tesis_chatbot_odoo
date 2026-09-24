# Almacenamiento en disco D:

Este documento explica cómo mantener **todos los datos importantes** del proyecto Odoo 18 en `D:` y minimizar el uso de `C:`.

## Mapa de almacenamiento

### En D: (obligatorio)

| Dato | Ruta física |
|------|-------------|
| Proyecto completo | `D:\odoo18-community-chatbot\` |
| Datos PostgreSQL | `D:\odoo18-community-chatbot\runtime\postgres\` |
| Filestore Odoo | `D:\odoo18-community-chatbot\runtime\odoo\` |
| Logs | `D:\odoo18-community-chatbot\runtime\logs\` |
| Addons personalizados | `D:\odoo18-community-chatbot\addons\custom\` |
| Respaldos | `D:\odoo18-community-chatbot\backups\` |
| Temporales scripts | `D:\odoo18-community-chatbot\tmp\` |
| Imagen disco Docker | `D:\DockerData\` (recomendado) |
| Distribución WSL | `D:\WSL\Ubuntu-24.04\` (recomendado) |

### En C: (mínimo inevitable)

| Dato | Motivo |
|------|--------|
| `C:\Program Files\Docker\` | Instalador oficial |
| `C:\Windows\System32\wsl.exe` | Componente Windows |
| `%APPDATA%\Docker\settings*.json` | Configuración pequeña (~KB) |
| Registro Windows / WSL metadata | Requerido por el SO |

> Con ~7 GB libres en C:, **no descargue imágenes Docker** hasta mover Docker Desktop a D:.

---

## Estrategia de bind mounts

El proyecto usa **bind mounts relativos** en `docker-compose.yml`:

```yaml
./runtime/postgres:/var/lib/postgresql/data
./runtime/odoo:/var/lib/odoo
./runtime/logs:/var/log/odoo
```

Esto garantiza que los datos sean visibles directamente en `D:\odoo18-community-chatbot\runtime\`.

### Compatibilidad NTFS + PostgreSQL

PostgreSQL en bind mounts de Windows puede fallar por permisos. Mitigaciones aplicadas:

1. `PGDATA` apunta a subcarpeta `pgdata` dentro del mount
2. Docker Desktop con backend WSL2 almacenado en D:
3. Si persisten errores, alternativa documentada: volúmenes Docker con disk image en D:

**Alternativa elegida:** bind mounts en D: con PGDATA en subcarpeta, asumiendo Docker Desktop WSL2 en D:.

---

## Mover Docker Desktop a D:

### Método oficial (recomendado)

1. Detenga contenedores: `docker compose down`
2. `wsl --shutdown`
3. Cierre Docker Desktop (Quit desde bandeja)
4. Abra **Docker Desktop → Settings → Resources → Advanced**
5. **Disk image location:** `D:\DockerData`
6. **Apply & Restart**
7. Verifique:

```powershell
Get-ChildItem D:\DockerData -Filter *.vhdx -Recurse
docker system df
```

### Si la UI no permite cambiar ubicación

En versiones recientes, la opción está en Settings → Resources → Advanced.
Si no aparece:

1. Exporte imágenes importantes: `docker save`
2. Desinstale Docker Desktop
3. Reinstale y configure `D:\DockerData` antes de la primera ejecución

**No mueva manualmente** archivos `.vhdx` mientras Docker está ejecutándose.

---

## Mover WSL2 a D:

### Exportar / importar (seguro)

```powershell
wsl --list --verbose
wsl --shutdown

# Exportar (verificar que el .tar existe y tiene tamaño > 0)
wsl --export Ubuntu-24.04 D:\WSL\backup\Ubuntu-24.04.tar

# Solo después de verificar el backup:
wsl --unregister Ubuntu-24.04
wsl --import Ubuntu-24.04 D:\WSL\Ubuntu-24.04 D:\WSL\backup\Ubuntu-24.04.tar --version 2
```

### Verificar

```powershell
wsl --list --verbose
Get-ChildItem D:\WSL\Ubuntu-24.04 -Filter ext4.vhdx -Recurse
wsl -d Ubuntu-24.04 -- echo "OK"
```

---

## Verificar ubicación de datos

Ejecute regularmente:

```powershell
Set-Location D:\odoo18-community-chatbot
.\scripts\check-storage.ps1
Get-PSDrive C, D
docker system df
wsl --list --verbose
```

Inspeccionar bind mounts activos:

```powershell
docker inspect odoo18-chatbot-db --format '{{json .Mounts}}' | ConvertFrom-Json
docker inspect odoo18-chatbot-odoo --format '{{json .Mounts}}' | ConvertFrom-Json
```

---

## Evitar que Docker consuma C:

1. Configure **Disk image location** en `D:\DockerData`
2. Mantenga WSL distros en `D:\WSL\`
3. Use `D:\odoo18-community-chatbot\tmp` para temporales en scripts
4. No use `%TEMP%` ni `%LOCALAPPDATA%` para dumps de base de datos
5. Ejecute `check-storage.ps1` antes de cada despliegue

---

## Limpieza segura de residuos en C:

### Solo después de verificar que todo funciona en D:

```powershell
# Ver qué ocuparía (NO elimina)
Get-ChildItem "$env:LOCALAPPDATA\Docker" -Recurse -ErrorAction SilentlyContinue | Measure-Object Length -Sum
Get-ChildItem "$env:LOCALAPPDATA\Packages\*Canonical*" -Recurse -ErrorAction SilentlyContinue | Measure-Object Length -Sum
```

### Carpetas que NO debe eliminar manualmente

- `C:\Program Files\Docker\`
- `C:\Windows\System32\`
- `D:\DockerData\` (datos activos)
- `D:\odoo18-community-chatbot\runtime\` (datos activos)
- Cualquier `.vhdx` en uso

### Limpieza segura de Docker (datos en D:)

```powershell
docker system prune   # Solo imágenes/contenedores no usados
# NO ejecute: docker volume prune (sin revisar primero)
```

Antes de `docker volume prune`, liste volúmenes:

```powershell
docker volume ls
docker volume inspect <nombre>
```

---

## Script de verificación

`scripts\check-storage.ps1` valida:

- Proyecto en D:
- Carpetas runtime en D:
- `.env` sin rutas C:
- Docker disk image en D: (si detectable)
- WSL en D: (si detectable)
- Espacio disponible en D:
- Advertencia si C: tiene poco espacio

Si detecta rutas críticas en C:, **detiene el despliegue** con código de salida 1.

---

## Residuos residuales esperados en C:

Tras configuración correcta, C: solo debería crecer con:

- Actualizaciones de Windows
- Configuración JSON de Docker Desktop (< 1 MB)
- Ejecutables de aplicaciones

Si `C:\Users\<usuario>\AppData\Local\Docker\wsl\` crece a GB, Docker no está correctamente en D: — repita la migración.
