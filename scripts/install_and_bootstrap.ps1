<#
Installer + Bootstrap (PowerShell)

Uso:
  Ejecuta este script en la máquina del usuario final. Descargará o clonará el repositorio
  y ejecutará `scripts/bootstrap.ps1` dentro del proyecto para instalar Python, venv,
  dependencias y Playwright.

Parámetros:
  -RepoUrl  URL del repositorio Git (por defecto: https://github.com/constadinisio/Huntly.js.git)
  -InstallDir Ruta donde instalar/clonar (por defecto: $env:USERPROFILE\Huntly.js)
  -Force    Fuerza re-descarga si la carpeta ya existe

Ejemplo:
  .\install_and_bootstrap.ps1 -InstallDir C:\Temp\Huntly -Force
#>

param(
    [string]$RepoUrl = 'https://github.com/constadinisio/Huntly.js.git',
    [string]$InstallDir = (Join-Path $env:USERPROFILE 'Huntly.js'),
    [switch]$Force
)

function Info($m){ Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Ok($m){ Write-Host "[OK]   $m" -ForegroundColor Green }
function Warn($m){ Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Err($m){ Write-Host "[ERROR] $m" -ForegroundColor Red }

Set-StrictMode -Version Latest

try {
    Info "Destino de instalación: $InstallDir"

    if (Test-Path $InstallDir) {
        if ($Force) {
            Info "Eliminando carpeta existente por -Force..."
            Remove-Item -Recurse -Force -Path $InstallDir
        } else {
            Info "Carpeta ya existe y -Force no fue especificado. Saltando descarga/clon."
        }
    }

    if (-not (Test-Path $InstallDir)) {
        # Preferir git clone si está disponible
        $git = Get-Command git -ErrorAction SilentlyContinue
        if ($git) {
            Info "Git encontrado. Clonando $RepoUrl -> $InstallDir"
            git clone $RepoUrl $InstallDir
        } else {
            Info "Git no disponible. Descargando ZIP desde GitHub..."
            $base = $RepoUrl -replace '\.git$',''
            $zipUrl = "$base/archive/refs/heads/main.zip"
            $tmp = Join-Path $env:TEMP "repo-main.zip"
            Info "Descargando $zipUrl"
            Invoke-WebRequest -Uri $zipUrl -OutFile $tmp -UseBasicParsing
            Info "Extrayendo a $env:TEMP"
            $extractDir = Join-Path $env:TEMP "huntly_repo_extracted"
            if (Test-Path $extractDir) { Remove-Item -Recurse -Force $extractDir }
            New-Item -ItemType Directory -Path $extractDir | Out-Null
            Expand-Archive -Path $tmp -DestinationPath $extractDir -Force
            Remove-Item $tmp -Force

            # GitHub zip extrae a repo-main
            $children = Get-ChildItem -Path $extractDir | Where-Object { $_.PSIsContainer }
            if ($children.Count -eq 1) {
                Move-Item -Path $children[0].FullName -Destination $InstallDir
            } else {
                Move-Item -Path (Join-Path $extractDir '*') -Destination $InstallDir
            }
            Remove-Item -Recurse -Force $extractDir
        }
        Ok "Código descargado en $InstallDir"
    }

    # Ejecutar el bootstrap del repo descargado
    $bootstrap = Join-Path $InstallDir 'scripts\bootstrap.ps1'
    if (-not (Test-Path $bootstrap)) {
        Err "No se encontró $bootstrap. Asegúrate de que el repo contiene scripts/bootstrap.ps1"
        exit 1
    }

    Info "Ejecutando bootstrap dentro de $InstallDir"
    Push-Location $InstallDir
    try {
        # Llamar a bootstrap con ejecución bypass para evitar restricciones
        & powershell -ExecutionPolicy Bypass -File $bootstrap
    } finally {
        Pop-Location
    }

    Ok "Instalación completa. Revisa config\\.env y ejecuta 'python main.py' si todo está listo."

} catch {
    Err "Error en installer: $_"
    exit 1
}
