Param(
  [switch]$Clean
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$venvPython = Join-Path $root ".venv\Scripts\python.exe"
$pyinstallerExe = Join-Path $root ".venv\Scripts\pyinstaller.exe"
$outputName = "天枢智元-融谈Copilot"

if (-not (Test-Path $venvPython)) {
  & "$PSScriptRoot\setup.ps1"
}

Write-Host "Installing desktop packaging dependencies..."
& $venvPython -m pip install -r requirements-desktop.txt

if ($Clean) {
  if (Test-Path "$root\build") {
    Remove-Item "$root\build" -Recurse -Force
  }
  if (Test-Path "$root\dist\$outputName") {
    Remove-Item "$root\dist\$outputName" -Recurse -Force
  }
}

$arguments = @(
  "--noconfirm",
  "--clean",
  "--windowed",
  "--onedir",
  "--name", $outputName,
  "--collect-submodules", "uvicorn",
  "--collect-all", "faster_whisper",
  "--collect-all", "ctranslate2",
  "--collect-all", "tokenizers",
  "--collect-all", "av",
  "--collect-all", "webview",
  "--add-data", "app\static;app\static",
  "--add-data", "samples;samples",
  "--add-data", "VERSION;.",
  "desktop_app.py"
)

Write-Host "Building desktop package..."
& $pyinstallerExe @arguments

$distDir = Join-Path $root "dist\$outputName"
Copy-Item "$root\settings.example.json" "$distDir\settings.example.json" -Force

Write-Host ""
Write-Host "Desktop package ready:"
Write-Host "  $distDir"
Write-Host ""
Write-Host "Entry executable:"
Write-Host "  $distDir\$outputName.exe"
