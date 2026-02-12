<#
Run main.py from the repository: activate .venv if present, otherwise use system python.

Usage:
  Right-click and "Run with PowerShell", or from PowerShell:
    .\scripts\run_main.ps1
#>

Set-StrictMode -Version Latest

function Info($m){ Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Warn($m){ Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Err($m){ Write-Host "[ERROR] $m" -ForegroundColor Red }

$scriptDir = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
$repoRoot = Resolve-Path (Join-Path $scriptDir '..')
Set-Location $repoRoot

Info "Repositorio: $repoRoot"

$activate = Join-Path $repoRoot '.venv\Scripts\Activate.ps1'
if (Test-Path $activate) {
    Info "Activando virtualenv (.venv)..."
    & $activate
} else {
    Warn "Virtualenv no encontrado en .venv — se usará python del sistema si está disponible."
}

$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Err "No se encontró 'python' en PATH. Ejecuta scripts\bootstrap.ps1 primero o instala Python."
    exit 1
}

Info "Ejecutando main.py..."
try {
    & python main.py
} catch {
    Err "Fallo al ejecutar main.py: $_"
    exit 1
}
