# Investor Conversation Copilot

`Investor Conversation Copilot` is a demoable AI product for fundraising and investor meeting analysis.

It helps founders and fundraising teams turn repeated investor conversations into reusable operating assets:

- investor question library
- answer quality review
- personal speaking style analysis
- canonical answers for onboarding
- team-wide training scripts

Current public demo version: `0.2.0`

## What It Does

- Accepts pasted transcripts or uploaded audio files.
- Supports in-browser recording for quick demo capture.
- Uses local `faster-whisper` for speech-to-text.
- Optionally uses Moonshot / Kimi to improve transcript normalization and meeting analysis.
- Extracts investor questions and founder answers.
- Reviews answer quality across completeness, clarity, consistency, and evidence.
- Summarizes speaking style and recurring communication patterns.
- Builds a topic library, canonical answers, and onboarding scripts from cumulative meeting history.

## Product Positioning

This is not a generic meeting notes tool.

The product is designed as a fundraising knowledge system:

1. Capture investor conversations.
2. Reconstruct structured Q&A.
3. Review whether the answer actually addressed the investor concern.
4. Build an evolving internal answer base.
5. Generate consistent training scripts for new team members.

## Stack

- Backend: `FastAPI`
- Frontend: `HTML + CSS + JavaScript`
- Storage: local JSON state store
- ASR: `faster-whisper`
- Optional LLM enhancement: Moonshot / Kimi
- Tests: `pytest`

## Quick Start

1. Create a virtual environment.

```powershell
py -m venv .venv
```

2. Install dependencies.

```powershell
.\.venv\Scripts\python -m pip install -r requirements.txt
```

3. Optional: configure Moonshot / Kimi.

```powershell
$env:MOONSHOT_API_KEY="replace-with-your-key"
$env:MOONSHOT_BASE_URL="https://api.moonshot.cn/v1"
$env:MOONSHOT_MODEL="kimi-latest"
```

4. Optional: configure local ASR.

```powershell
$env:ASR_MODEL_SIZE="small"
$env:ASR_DEVICE="cpu"
$env:ASR_COMPUTE_TYPE="int8"
```

5. Start the app.

```powershell
.\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

6. Open the demo in a browser.

```text
http://127.0.0.1:8000
```

For Windows demos, prefer the command above instead of `--reload`, because stale reload processes can leave the port in a confusing state.

## Demo Paths

- Load the sample transcript from [`samples/fundraising_transcript.txt`](samples/fundraising_transcript.txt)
- Paste your own transcript
- Upload an audio file
- Record directly in the browser

## Runtime Health

Check runtime status at:

- `GET /api/health`

The response includes:

- `status`
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

Interactive API docs:

- `http://127.0.0.1:8000/docs`

## Project Structure

- `app/`: API, services, models, and static workbench
- `docs/`: architecture and pipeline notes
- `samples/`: sample fundraising transcript
- `tests/`: API and workflow tests
- `scripts/`: local setup and run helpers

## Public Repo Conventions

- Version is tracked in [`VERSION`](VERSION) and surfaced by the app health endpoint.
- User-facing changes should be recorded in [`CHANGELOG.md`](CHANGELOG.md).
- Planned next-stage work is tracked in [`ROADMAP.md`](ROADMAP.md).
- Contribution flow is documented in [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Share With Teammates

Use the following helper files when sharing internally:

- [`COLLEAGUE_SETUP.md`](COLLEAGUE_SETUP.md)
- [`start-demo.bat`](start-demo.bat)
- [`scripts/setup.ps1`](scripts/setup.ps1)
- [`scripts/run-demo.ps1`](scripts/run-demo.ps1)
- [`scripts/env.example.ps1`](scripts/env.example.ps1)

## Security Notes

- Never commit API keys to the repository.
- Always provide Moonshot / Kimi credentials through environment variables.
- Rotate any key that was ever pasted into chat logs or screenshots.

## Docs

- [`docs/architecture.md`](docs/architecture.md)
- [`docs/data-model-and-pipeline.md`](docs/data-model-and-pipeline.md)
- [`ROADMAP.md`](ROADMAP.md)
- [`CHANGELOG.md`](CHANGELOG.md)

