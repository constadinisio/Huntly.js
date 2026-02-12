<#
Bootstrap script (Windows PowerShell)

Qué hace:
- Verifica si `python` está disponible; si no, descarga e instala un instalador oficial de Python (silencioso).
- Crea y activa un virtualenv `.venv` en el repo.
- Actualiza `pip` y instala dependencias desde `requirements.txt`.
- Instala navegadores necesarios para Playwright.
- Copia `config/.env.example` → `config/.env` si no existe.

Notas:
- Ejecutar desde la raíz del repo en PowerShell (ejecuta como Administrador si quieres que la instalación de Python sea para todos los usuarios).
#>

Param(
    [string]$PythonUrl = 'https://www.python.org/ftp/python/3.11.4/python-3.11.4-amd64.exe'
)

function Write-Info($m){ Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Write-Ok($m){ Write-Host "[OK]   $m" -ForegroundColor Green }
function Write-Warn($m){ Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Write-Err($m){ Write-Host "[ERROR] $m" -ForegroundColor Red }

Set-StrictMode -Version Latest

try {
    Write-Info "Comprobando existencia de Python..."
    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) {
        Write-Warn "Python no encontrado en PATH. Intentando descargar e instalar Python desde: $PythonUrl"
        $tmp = Join-Path $env:TEMP "python-installer.exe"
        Write-Info "Descargando instalador a $tmp"
        Invoke-WebRequest -Uri $PythonUrl -OutFile $tmp -UseBasicParsing

        Write-Info "Ejecutando instalador (silencioso). Esto puede tardar..."
        $args = '/quiet InstallAllUsers=1 PrependPath=1 Include_pip=1'
        $proc = Start-Process -FilePath $tmp -ArgumentList $args -Wait -PassThru -ErrorAction Stop
        if ($proc.ExitCode -ne 0) {
            Write-Warn "Instalación de Python devolvió código $($proc.ExitCode). Intentando instalación para usuario actual..."
            $args2 = '/quiet InstallAllUsers=0 PrependPath=1 Include_pip=1'
            Start-Process -FilePath $tmp -ArgumentList $args2 -Wait -PassThru
        }
        Remove-Item $tmp -Force -ErrorAction SilentlyContinue

        # refrescar PATH en la sesión actual
        $machinePath = [System.Environment]::GetEnvironmentVariable('Path','Machine')
        $userPath = [System.Environment]::GetEnvironmentVariable('Path','User')
        $env:Path = ($machinePath + ';' + $userPath).TrimEnd(';')

        $py = Get-Command python -ErrorAction SilentlyContinue
        if (-not $py) {
            Write-Err "No se pudo localizar `python` tras la instalación. Reinicia PowerShell o añade Python al PATH manualmente."
            exit 1
        }
        Write-Ok "Python instalado. Versión: $(python --version)"
    }

    Write-Info "Creando virtualenv en .venv (si no existe)..."
    if (-not (Test-Path .venv)) {
        python -m venv .venv
        Write-Ok "Virtualenv creado en .venv"
    } else {
        Write-Info "Virtualenv ya existe, usándolo."
    }

    Write-Info "Activando virtualenv y actualizando pip..."
    $activate = Join-Path (Resolve-Path .venv).Path 'Scripts\Activate.ps1'
    if (Test-Path $activate) {
        & $activate
    } else {
        Write-Err "No se encontró $activate"
        exit 1
    }

    Write-Info "Actualizando pip, setuptools y wheel..."
    pip install -U pip setuptools wheel

    if (Test-Path 'requirements.txt') {
        Write-Info "Instalando dependencias desde requirements.txt..."
        pip install -r requirements.txt
    } else {
        Write-Warn "No se encontró requirements.txt; omitiendo instalación de dependencias."
    }

    Write-Info "Instalando navegadores Playwright..."
    try {
        python -m playwright install
        Write-Ok "Playwright instalado."
    } catch {
        Write-Warn "Error instalando Playwright: $_. Exception.Message"
    }

    if (-not (Test-Path 'config')) {
        Write-Info "Creando carpeta config/"
        New-Item -ItemType Directory -Path config | Out-Null
    }

    if (-not (Test-Path 'config\\.env')) {
        if (Test-Path 'config\\.env.example') {
            Copy-Item 'config\\.env.example' 'config\\.env'
            Write-Ok "Se creó config/.env desde config/.env.example. Edita valores sensibles antes de ejecutar."
        } else {
            Write-Warn "No existe config/.env.example — crea config/.env manualmente."
        }
    } else {
        Write-Info "config/.env ya existe — no se sobrescribe."
    }

    # Determine WORKANA_STATE_FILE from config/.env if present, otherwise default
    $defaultState = 'config\workana_state.json'
    $stateFile = $defaultState
    if (Test-Path 'config\.env') {
        $envLines = Get-Content 'config\.env'
        foreach ($l in $envLines) {
            if ($l -match '^\s*WORKANA_STATE_FILE\s*=\s*(.+)\s*$') {
                $val = $matches[1].Trim()
                $val = $val.Trim("'\"")
                if ($val -ne '') { $stateFile = $val }
                break
            }
        }
    }

    Write-Info "Se usará WORKANA_STATE_FILE: $stateFile"

    $answer = Read-Host "¿Deseas ejecutar ahora el bootstrap de Playwright para iniciar sesión en Workana y guardar el estado en $stateFile? (y/N)"
    if ($answer -and $answer.Substring(0,1).ToLower() -eq 'y') {
        Write-Info "Ejecutando: python -m huntly.workana.bootstrap"
        try {
            & python -m huntly.workana.bootstrap
        } catch {
            Write-Warn "El comando python -m huntly.workana.bootstrap devolvió un error: $_"
        }

        if (Test-Path $stateFile) {
            Write-Ok "Playwright storage state guardado en: $stateFile"
        } else {
            Write-Warn "No se encontró $stateFile después de ejecutar el bootstrap. Si el navegador se abrió, completa el login en Workana y verifica la ruta manualmente."
        }
    } else {
        Write-Info "Omitido bootstrap Playwright. Para completo manualmente: python -m huntly.workana.bootstrap"
    }

    Write-Ok "Bootstrap local finalizado. Luego inicia la app: \n  python main.py"

} catch {
    Write-Err "Error durante el bootstrap: $_"
    exit 1
}
