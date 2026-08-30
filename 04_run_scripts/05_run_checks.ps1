$ErrorActionPreference = "Stop"

$packageRoot = Split-Path -Parent $PSScriptRoot
$projectDir = Join-Path $packageRoot "01_source_main_demo\fraud-pet-demo"
$backendDir = Join-Path $projectDir "backend"
$venvPython = Join-Path $backendDir ".venv\Scripts\python.exe"

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string] $FilePath,
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]] $Arguments
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $FilePath $($Arguments -join ' ')"
    }
}

Write-Host "1/3 Running backend API tests"
Set-Location $backendDir
if (Test-Path -LiteralPath $venvPython) {
    Invoke-CheckedCommand $venvPython -m pytest tests -q
} else {
    Invoke-CheckedCommand python -m pytest tests -q
}

Write-Host ""
Write-Host "2/3 Running frontend tests"
Set-Location $projectDir
Invoke-CheckedCommand npm.cmd test

Write-Host ""
Write-Host "3/3 Running frontend production build"
Invoke-CheckedCommand npm.cmd run build

Write-Host ""
Write-Host "Checks completed."
