$ErrorActionPreference = "Stop"

$packageRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $packageRoot "01_source_main_demo\fraud-pet-demo\backend"
$venvPython = Join-Path $backendDir ".venv\Scripts\python.exe"

Set-Location $backendDir

if (Test-Path -LiteralPath $venvPython) {
    $python = $venvPython
} else {
    $python = "python"
}

Write-Host "Starting backend API: http://127.0.0.1:8000"
& $python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
