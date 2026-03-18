Param(
  [string]$MoonshotApiKey = "",
  [string]$MoonshotBaseUrl = "https://api.moonshot.cn/v1",
  [string]$MoonshotModel = "kimi-latest",
  [string]$AsrModelSize = "small"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
  Write-Host "Virtual environment not found. Running setup first..."
  & "$PSScriptRoot\setup.ps1"
}

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

Write-Host "Starting Investor Conversation Copilot..."
Write-Host "Open http://127.0.0.1:8000 after the server is ready."
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

