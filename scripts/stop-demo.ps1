Param(
  [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

function Get-DemoProcesses {
  param([int]$PortNumber)
  Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match "^python" -and
    $_.CommandLine -like "*uvicorn app.main:app*" -and
    $_.CommandLine -like "*--port $PortNumber*"
  }
}

$processes = @(Get-DemoProcesses -PortNumber $Port)
if ($processes.Count -eq 0) {
  Write-Host "No demo process found on port $Port."
  exit 0
}

foreach ($process in $processes) {
  Stop-Process -Id $process.ProcessId -Force
}

Write-Host "Stopped Investor Conversation Copilot on port $Port."
