Param()

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
  Write-Host "Creating virtual environment..."
  py -m venv .venv
}

Write-Host "Installing dependencies..."
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

Write-Host "Setup complete."

