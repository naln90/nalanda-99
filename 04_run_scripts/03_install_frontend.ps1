$ErrorActionPreference = "Stop"

$packageRoot = Split-Path -Parent $PSScriptRoot
$frontendDir = Join-Path $packageRoot "01_source_main_demo\fraud-pet-demo"

Set-Location $frontendDir

npm.cmd ci

Write-Host ""
Write-Host "Frontend dependencies installed."
