Param(
  [string]$MoonshotApiKey = "",
  [string]$MoonshotBaseUrl = "https://api.moonshot.cn/v1",
  [string]$MoonshotModel = "kimi-latest",
  [string]$AsrModelSize = "small",
  [string]$AsrDevice = "cpu",
  [string]$AsrComputeType = "int8",
  [int]$Port = 8000,
  [switch]$ForceRestart,
  [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Get-HealthUrl {
  param([int]$PortNumber)
  return "http://127.0.0.1:$PortNumber/api/health"
}

function Get-DemoProcesses {
  param([int]$PortNumber)
  Get-CimInstance Win32_Process | Where-Object {
    $_.Name -match "^python" -and
    $_.CommandLine -like "*uvicorn app.main:app*" -and
    $_.CommandLine -like "*--port $PortNumber*"
  }
}

function Get-DemoHealth {
  param([int]$PortNumber)
  try {
    return Invoke-RestMethod (Get-HealthUrl -PortNumber $PortNumber) -TimeoutSec 2
  } catch {
    return $null
  }
}

function Stop-DemoProcesses {
  param([int]$PortNumber)
  $processes = @(Get-DemoProcesses -PortNumber $PortNumber)
  foreach ($process in $processes) {
    Stop-Process -Id $process.ProcessId -Force
  }
}

$envFile = Join-Path $PSScriptRoot "env.local.ps1"
if (Test-Path $envFile) {
  . $envFile
}

& "$PSScriptRoot\setup.ps1"

if ($MoonshotApiKey) {
  $env:MOONSHOT_API_KEY = $MoonshotApiKey
}
if ($MoonshotBaseUrl) {
  $env:MOONSHOT_BASE_URL = $MoonshotBaseUrl
}
if ($MoonshotModel) {
  $env:MOONSHOT_MODEL = $MoonshotModel
}
if ($AsrModelSize) {
  $env:ASR_MODEL_SIZE = $AsrModelSize
}
if ($AsrDevice) {
  $env:ASR_DEVICE = $AsrDevice
}
if ($AsrComputeType) {
  $env:ASR_COMPUTE_TYPE = $AsrComputeType
}

if ($ForceRestart) {
  Stop-DemoProcesses -PortNumber $Port
  Start-Sleep -Seconds 1
}

$existingHealth = Get-DemoHealth -PortNumber $Port
if ($existingHealth -and $existingHealth.status -eq "ok") {
  Write-Host "Demo is already running on http://127.0.0.1:$Port"
  if (-not $NoBrowser) {
    Start-Process "http://127.0.0.1:$Port"
  }
  return
}

$runDir = Join-Path $root "data\run"
New-Item -ItemType Directory -Force -Path $runDir | Out-Null
$stdoutLog = Join-Path $runDir "uvicorn-$Port.out.log"
$stderrLog = Join-Path $runDir "uvicorn-$Port.err.log"

Write-Host "Starting Investor Conversation Copilot..."
$process = Start-Process `
  -FilePath ".\.venv\Scripts\python.exe" `
  -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "$Port") `
  -WorkingDirectory $root `
  -RedirectStandardOutput $stdoutLog `
  -RedirectStandardError $stderrLog `
  -PassThru

$ready = $false
for ($attempt = 0; $attempt -lt 45; $attempt++) {
  Start-Sleep -Seconds 1
  $health = Get-DemoHealth -PortNumber $Port
  if ($health -and $health.status -eq "ok") {
    $ready = $true
    break
  }
  if ($process.HasExited) {
    break
  }
}

if (-not $ready) {
  Write-Host "The demo server did not become ready in time."
  Write-Host "Check logs:"
  Write-Host "  $stdoutLog"
  Write-Host "  $stderrLog"
  if (Test-Path $stderrLog) {
    Write-Host "Recent error output:"
    Get-Content $stderrLog -Tail 20
  }
  exit 1
}

Write-Host "Demo is ready at http://127.0.0.1:$Port"
Write-Host "Logs:"
Write-Host "  $stdoutLog"
Write-Host "  $stderrLog"
if (-not $NoBrowser) {
  Start-Process "http://127.0.0.1:$Port"
}
