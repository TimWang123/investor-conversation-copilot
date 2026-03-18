# Colleague Setup Guide

[English](./COLLEAGUE_SETUP.en.md) | [简体中文](./COLLEAGUE_SETUP.md)

## Easiest Path

1. Double-click [`start-demo.bat`](./start-demo.bat)
2. The first run creates the virtual environment and installs dependencies automatically
3. Once the server is ready, the browser opens automatically
4. The default address is `http://127.0.0.1:8000`

To stop the server later:

1. Double-click [`stop-demo.bat`](./stop-demo.bat)

## If You Want Kimi Enabled

Recommended path:

1. Copy [`scripts/env.example.ps1`](./scripts/env.example.ps1) to `scripts/env.local.ps1`
2. Replace the placeholder values with your own settings
3. Double-click [`start-demo.bat`](./start-demo.bat) again

You can also launch manually:

```powershell
.\scripts\launch-demo.ps1 -MoonshotApiKey "your-key"
```

## If You Want Foreground Logs

```powershell
.\scripts\run-demo.ps1
```

## What You Can Try

- paste a transcript and generate a review
- upload an audio file and let the app transcribe it
- record directly in the browser and analyze the meeting
- inspect Q&A reviews, topic libraries, canonical answers, and training scripts

## Notes

- the first audio analysis may download the local `faster-whisper` model and take longer
- the app still works without Kimi and falls back to local rules
- if the browser does not open automatically, visit `http://127.0.0.1:8000` manually
