# Copy this file to scripts\env.local.ps1 and replace the placeholder values.
$env:LLM_PROVIDER="qwen"

# Qwen / DashScope
$env:QWEN_API_KEY="replace-with-your-key"
$env:QWEN_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
$env:QWEN_MODEL="qwen-plus"

# Moonshot / Kimi
$env:MOONSHOT_API_KEY="replace-with-your-key"
$env:MOONSHOT_BASE_URL="https://api.moonshot.cn/v1"
$env:MOONSHOT_MODEL="kimi-latest"
$env:ASR_MODEL_SIZE="small"
$env:ASR_DEVICE="cpu"
$env:ASR_COMPUTE_TYPE="int8"
