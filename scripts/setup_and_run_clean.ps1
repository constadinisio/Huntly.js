<#
Minimal, syntactically-clean installer for Windows (clean test file).

This test script clones/downloads the repository (if needed), ensures `config/.env`
exists (copies from example if available), optionally writes provided tokens
into `config/.env`, and creates a `.venv` only if `python` is present on PATH.
#>

param(
    [string]$RepoUrl = 'https://github.com/constadinisio/Huntly.js.git',
    [string]$InstallDir = (Join-Path $env:USERPROFILE 'Huntly.js'),
    [switch]$Force,
    [switch]$SkipBootstrap,
    [switch]$NonInteractive,
    [string]$TGToken,
    [string]$TGChat,
    [string]$OpenAIKey
)

function Info($m){ Write-Host "[INFO] $m" -ForegroundColor Cyan }
function Ok($m){ Write-Host "[OK]   $m" -ForegroundColor Green }
function Warn($m){ Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Err($m){ Write-Host "[ERROR] $m" -ForegroundColor Red }

Set-StrictMode -Version Latest

try {
    $scriptDir = Split-Path -Path $MyInvocation.MyCommand.Definition -Parent
    $possibleRepoRoot = Resolve-Path -LiteralPath (Join-Path $scriptDir '..') -ErrorAction SilentlyContinue
    if (-not $possibleRepoRoot) { $possibleRepoRoot = Get-Location }
    $possibleRepoRoot = $possibleRepoRoot.Path

    if (Test-Path (Join-Path $possibleRepoRoot 'huntly')) {
        $repoRoot = $possibleRepoRoot
    } else {
        if ((Test-Path $InstallDir) -and $Force) { Remove-Item -Recurse -Force -Path $InstallDir; Info "Removed existing $InstallDir" }
        if (-not (Test-Path $InstallDir)) {
            $git = Get-Command git -ErrorAction SilentlyContinue
            if ($git) {
                Info "Cloning $RepoUrl -> $InstallDir"
                git clone $RepoUrl $InstallDir
            } else {
                Info "Git not available: downloading zip"
                $base = $RepoUrl -replace '\.git$',''
                $zipUrl = "$base/archive/refs/heads/main.zip"
                $tmp = Join-Path $env:TEMP 'huntly-main.zip'
                Invoke-WebRequest -Uri $zipUrl -OutFile $tmp -UseBasicParsing
                $extractDir = Join-Path $env:TEMP 'huntly_extracted'
                if (Test-Path $extractDir) { Remove-Item -Recurse -Force $extractDir }
                New-Item -ItemType Directory -Path $extractDir | Out-Null
                Expand-Archive -Path $tmp -DestinationPath $extractDir -Force
                Remove-Item $tmp -Force
                $children = Get-ChildItem -Path $extractDir | Where-Object { $_.PSIsContainer }
                if ($children.Count -eq 1) { Move-Item -Path $children[0].FullName -Destination $InstallDir } else { Move-Item -Path (Join-Path $extractDir '*') -Destination $InstallDir }
                Remove-Item -Recurse -Force $extractDir
            }
            Ok "Repository ready at $InstallDir"
        } else { Info "Using existing folder $InstallDir" }
        $repoRoot = (Resolve-Path $InstallDir).Path
    }

    Push-Location $repoRoot

    # Ensure config/.env exists
    if (-not (Test-Path 'config')) { New-Item -ItemType Directory -Path config | Out-Null }
    if (-not (Test-Path 'config\.env')) {
        if (Test-Path 'config\.env.example') { Copy-Item 'config\.env.example' 'config\.env'; Ok 'Created config/.env from example' } else { Warn 'config/.env.example not found; please create config/.env' }
    } else { Info 'config/.env already exists' }

    # Read WORKANA_STATE_FILE if present
    $stateFile = 'config\workana_state.json'
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
    Info "WORKANA_STATE_FILE: $stateFile"

    # Minimal python handling: create venv only if python is available
    $py = Get-Command python -ErrorAction SilentlyContinue
    if ($py) {
        if (-not (Test-Path '.venv')) { Info 'Creating virtualenv .venv'; python -m venv .venv; Ok 'Virtualenv created' } else { Info '.venv already exists' }
    } else {
        Warn 'Python not found in PATH. Skipping venv creation and package installs.'
    }

    # Update config/.env with provided tokens
    function Set-EnvValue($key, $value) {
        if (-not $value) { return }
        $envPath = Join-Path (Get-Location) 'config\.env'
        if (-not (Test-Path $envPath)) { New-Item -ItemType File -Path $envPath -Force | Out-Null }
        $content = Get-Content $envPath -Raw
        $pattern = "(?m)^\s*" + [regex]::Escape($key) + "\s*=.*$"
        if ($content -match $pattern) { $new = [regex]::Replace($content, $pattern, "$key=$value") } else { $new = $content.TrimEnd() + [Environment]::NewLine + "$key=$value" + [Environment]::NewLine }
        Set-Content -Path $envPath -Value $new -Force
        Info "Updated $key in config/.env"
    }

    if ($TGToken) { Set-EnvValue 'TG_TOKEN' $TGToken }
    if ($TGChat)  { Set-EnvValue 'TG_CHAT' $TGChat }
    if ($OpenAIKey) { Set-EnvValue 'OPENAI_API_KEY' $OpenAIKey }

    Pop-Location
    Ok 'Setup finished successfully.'

} catch {
    Err "Error in setup_and_run: $_"
    exit 1
}
