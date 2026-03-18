Param(
  [string]$MoonshotApiKey = "",
  [string]$MoonshotBaseUrl = "https://api.moonshot.cn/v1",
  [string]$MoonshotModel = "kimi-latest",
  [string]$AsrModelSize = "small",
  [string]$AsrDevice = "cpu",
  [string]$AsrComputeType = "int8",
  [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

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

Write-Host "Starting Investor Conversation Copilot in the current window..."
Write-Host "Open http://127.0.0.1:$Port after the server is ready."
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port $Port
