$ErrorActionPreference = "Stop"

$packageRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $packageRoot "01_source_main_demo\fraud-pet-demo\backend"

Set-Location $backendDir

if (-not (Test-Path -LiteralPath ".venv")) {
    python -m venv .venv
}

$python = Join-Path $backendDir ".venv\Scripts\python.exe"
& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt

Write-Host ""
Write-Host "Backend dependencies installed."
