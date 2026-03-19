$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$desktopFolder = Get-ChildItem -Path (Join-Path $repoRoot "dist") |
    Where-Object { $_.PSIsContainer -and $_.Name -like "*Copilot*" } |
    Select-Object -First 1

if (-not $desktopFolder) {
    throw "Desktop build folder not found under dist."
}

$version = (Get-Content -Path (Join-Path $repoRoot "VERSION") -Raw).Trim()
$zipPath = Join-Path $desktopFolder.Parent.FullName ("Tianshu-RongtanCopilot-windows-v{0}.zip" -f $version)

if (Test-Path $zipPath) {
    Remove-Item -Path $zipPath -Force
}

Compress-Archive -Path (Join-Path $desktopFolder.FullName "*") -DestinationPath $zipPath -Force
Write-Output $zipPath
