param(
    [string]$InstallDir = (Join-Path $env:TEMP 'huntly_test')
)

Write-Host "[INFO] Test installer starting"

if (-not (Test-Path $InstallDir)) {
    $git = Get-Command git -ErrorAction SilentlyContinue
    if ($git) {
        Write-Host "[INFO] Cloning into $InstallDir"
        git clone 'https://github.com/constadinisio/Huntly.js.git' $InstallDir
    } else {
        Write-Host "[INFO] Git not found, downloading ZIP"
        $zip = Join-Path $env:TEMP 'huntly_test.zip'
        Invoke-WebRequest -Uri 'https://github.com/constadinisio/Huntly.js/archive/refs/heads/main.zip' -OutFile $zip -UseBasicParsing
        Expand-Archive -Path $zip -DestinationPath $InstallDir -Force
        Remove-Item $zip -Force
    }
    Write-Host "[OK] Repo available at $InstallDir"
} else { Write-Host "[INFO] Using existing $InstallDir" }

if (-not (Test-Path (Join-Path $InstallDir 'config'))) { New-Item -ItemType Directory -Path (Join-Path $InstallDir 'config') | Out-Null }
if ((Test-Path (Join-Path $InstallDir 'config\.env.example')) -and -not (Test-Path (Join-Path $InstallDir 'config\.env'))) {
    Copy-Item (Join-Path $InstallDir 'config\.env.example') (Join-Path $InstallDir 'config\.env')
    Write-Host "[OK] Created config/.env from example"
} else { Write-Host "[INFO] config/.env present or example missing" }

Write-Host "[INFO] Test installer finished"
