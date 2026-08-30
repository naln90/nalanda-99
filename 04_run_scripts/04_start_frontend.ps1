$ErrorActionPreference = "Stop"

$packageRoot = Split-Path -Parent $PSScriptRoot
$frontendDir = Join-Path $packageRoot "01_source_main_demo\fraud-pet-demo"

Set-Location $frontendDir

$env:VITE_API_BASE_URL = "http://127.0.0.1:8000/api"

Write-Host "Starting frontend page: http://127.0.0.1:5173"
npm.cmd run dev -- --host 127.0.0.1 --port 5173
