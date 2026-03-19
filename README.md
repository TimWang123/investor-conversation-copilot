<div align="center">
  <h1>天枢智元·融谈Copilot</h1>
  <p><strong>Investor Conversation Copilot</strong></p>
  <p>Turn investor meetings into structured Q&A, answer reviews, reusable team messaging, and onboarding scripts.</p>
  <p>
    <a href="./README.md">English</a> |
    <a href="./README.zh-CN.md">简体中文</a>
  </p>
  <p>
    <img alt="Status" src="https://img.shields.io/badge/status-public%20demo-1f8b4c" />
    <img alt="Version" src="https://img.shields.io/badge/version-0.3.0-0A66C2" />
    <img alt="Backend" src="https://img.shields.io/badge/backend-FastAPI-05998b" />
    <img alt="ASR" src="https://img.shields.io/badge/asr-faster--whisper-5C6BC0" />
    <img alt="LLM" src="https://img.shields.io/badge/llm-Kimi%20optional-F97316" />
  </p>
</div>

## Why This Exists

Founders and fundraising teams answer the same investor questions over and over, but the answers rarely get preserved as a consistent operating asset.

This project turns those repeated conversations into:

- structured investor question libraries
- answer quality reviews
- speaking style summaries
- canonical team answers
- onboarding scripts for new teammates

## Product Flow

```mermaid
flowchart LR
    A["Audio or Transcript"] --> B["Transcription and Normalization"]
    B --> C["Investor Q&A Extraction"]
    C --> D["Answer Review"]
    D --> E["Topic Library"]
    D --> F["Canonical Answers"]
    D --> G["Training Scripts"]
```

## Product Snapshot

| Area | What the demo already does |
| --- | --- |
| Input | Paste transcripts, upload audio, or record in the browser |
| Analysis | Extract investor questions and founder answers |
| Multi-party | Track named speakers across investor partners, CEO, CFO, and other attendees |
| Review | Score completeness, clarity, consistency, and evidence |
| Knowledge | Build topic libraries and reusable answer patterns |
| Enablement | Generate onboarding and training scripts |
| AI | Use local rules by default and switch to Moonshot / Kimi or Qwen when configured |

## Demo Highlights

- Transcript-first workflow for quick demos and low-friction testing
- Local `faster-whisper` transcription for audio uploads
- Optional Kimi-enhanced transcript normalization and answer review
- Runtime settings page for switching ASR size/device and the active LLM provider/model
- Topic and canonical-answer views for message consistency
- Multi-party meeting MVP with speaker-aware reviews and unanswered follow-up tracking
- Browser workbench designed for internal budget and product demos

## One-Click Local Demo

For the easiest Windows experience:

1. Double-click [`start-demo.bat`](./start-demo.bat)
2. Wait for setup and server startup
3. The browser opens automatically at `http://127.0.0.1:8000`

To stop the local server later:

- double-click [`stop-demo.bat`](./stop-demo.bat)

## Desktop Download

The GitHub "Download ZIP" button only downloads source code. It does not include the packaged `dist/` desktop app.

If you want a ready-to-run Windows package, download the release asset from the repository's **Releases** page.

## Windows Desktop Build

If you want a real desktop executable instead of a batch launcher:

1. Install desktop packaging dependencies.

```powershell
.\.venv\Scripts\python -m pip install -r requirements-desktop.txt
```

2. Build the desktop package.

```powershell
.\scripts\build-desktop.ps1 -Clean
```

3. Find the packaged app in:

```text
dist\天枢智元-融谈Copilot
```

4. Launch the packaged desktop app:

```text
dist\天枢智元-融谈Copilot\天枢智元-融谈Copilot.exe
```

The packaged desktop app runs the local service in the background and opens a native desktop window instead of a browser tab.

## Desktop App Settings

For packaged desktop builds, the app can read `settings.json` from the same folder as the exe.

Fastest path:

1. Copy [`settings.example.json`](./settings.example.json) to `settings.json`
2. Replace the placeholder values
3. Keep `settings.json` next to the packaged exe

This is the easiest way to let a teammate use the same Kimi model configuration without touching system environment variables.

## Manual Setup

1. Create a virtual environment.

```powershell
py -m venv .venv
```

2. Install dependencies.

```powershell
.\.venv\Scripts\python -m pip install -r requirements.txt
```

3. Optional: configure Moonshot / Kimi or Qwen.

```powershell
$env:LLM_PROVIDER="qwen"
$env:QWEN_API_KEY="replace-with-your-key"
$env:QWEN_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
$env:QWEN_MODEL="qwen3.5-plus"
```

For Moonshot / Kimi, switch `LLM_PROVIDER` to `moonshot` and use `MOONSHOT_API_KEY`, `MOONSHOT_BASE_URL`, and `MOONSHOT_MODEL`.

You can also switch the active provider and model directly in the app's settings page after startup.

4. Start the app in the current shell.

```powershell
.\scripts\run-demo.ps1
```

5. Open the demo.

```text
http://127.0.0.1:8000
```

## Optional Local Config

If you want the one-click launcher to use your preferred model settings automatically:

1. Copy [`scripts/env.example.ps1`](./scripts/env.example.ps1) to `scripts/env.local.ps1`
2. Replace the placeholder values
3. Run [`start-demo.bat`](./start-demo.bat)

`env.local.ps1` is ignored by git and stays local to each machine.

## Runtime Health

Runtime status is available at:

- `GET /api/health`

The response includes:

- `status`
- `app_name`
- `app_version`
- `llm_provider`
- `llm_enabled`
- `llm_model`
- `asr_provider`
- `asr_enabled`
- `asr_model`
- `asr_device`

## Main API Endpoints

- `GET /api/health`
- `GET /api/dashboard`
- `POST /api/meetings`
- `POST /api/meetings/from-audio`
- `GET /api/meetings`
- `GET /api/meetings/{id}`
- `GET /api/meetings/{id}/qa-exchanges`
- `GET /api/meetings/{id}/review`
- `GET /api/topics`
- `GET /api/topics/{topic_id}`
- `GET /api/topics/{topic_id}/canonical-answers`
- `GET /api/training-scripts/latest`

Interactive docs:

- `http://127.0.0.1:8000/docs`

## Repository Guide

- [Chinese README](./README.zh-CN.md)
- [Roadmap](./ROADMAP.md)
- [Chinese Roadmap](./ROADMAP.zh-CN.md)
- [Contributing](./CONTRIBUTING.md)
- [Chinese Contributing Guide](./CONTRIBUTING.zh-CN.md)
- [Changelog](./CHANGELOG.md)
- [Colleague Setup Guide (Chinese)](./COLLEAGUE_SETUP.md)
- [Colleague Setup Guide (English)](./COLLEAGUE_SETUP.en.md)
- [Desktop Build Guide](./DESKTOP_BUILD.md)
- [Desktop Build Guide (Chinese)](./DESKTOP_BUILD.zh-CN.md)
- [Architecture Notes](./docs/architecture.md)
- [Data Model and Pipeline](./docs/data-model-and-pipeline.md)
- [License (English)](./LICENSE)
- [License Explainer (Chinese)](./LICENSE.zh-CN.md)

## Security Notes

- Never commit API keys or local environment files
- Use environment variables or `settings.json` for Moonshot / Kimi / Qwen credentials
- Rotate any key that has ever been pasted into chat logs or screenshots

## License

This repository is public for showcase and evaluation, but it is not open source.

- Rights are reserved by default under [`LICENSE`](./LICENSE)
- Reuse, redistribution, derivative development, or commercial use require permission
- For licensing or partnership requests, contact the repository owner through GitHub
