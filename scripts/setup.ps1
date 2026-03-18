Param(
  [switch]$ForceInstall
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$venvPython = Join-Path $root ".venv\Scripts\python.exe"
$requirementsFile = Join-Path $root "requirements.txt"
$stampFile = Join-Path $root ".venv\.requirements-installed"

if (-not (Test-Path $venvPython)) {
  Write-Host "Creating virtual environment..."
  py -m venv .venv
}

$needInstall = $ForceInstall -or -not (Test-Path $stampFile)
if (-not $needInstall) {
  $needInstall = (Get-Item $requirementsFile).LastWriteTimeUtc -gt (Get-Item $stampFile).LastWriteTimeUtc
}

if ($needInstall) {
  Write-Host "Installing dependencies..."
  & $venvPython -m pip install --upgrade pip
  & $venvPython -m pip install -r requirements.txt
  Set-Content -Path $stampFile -Value (Get-Date).ToString("o") -Encoding UTF8
} else {
  Write-Host "Dependencies already installed."
}

Write-Host "Setup complete."
