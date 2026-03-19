# Changelog

## [0.2.5] - 2026-03-18

### Added

- settings-page support for switching the active LLM provider and model name
- backend `/api/settings/llm` endpoint for persisting runtime LLM configuration
- regression coverage for saving Qwen model settings through the API

### Changed

- bumped the app version to `0.2.5`
- updated the runtime settings UI so ASR and LLM configuration can be changed independently
- improved freeform transcript follow-up question detection for multi-turn investor Q&A extraction

## [0.2.4] - 2026-03-18

### Added

- configurable `LLM_PROVIDER` switch for choosing Moonshot / Kimi or Qwen
- Qwen / DashScope OpenAI-compatible gateway support
- Qwen examples in environment and desktop settings templates

### Changed

- bumped the app version to `0.2.4`
- generalized the LLM integration from a Moonshot-only path to a provider-based path

## [0.2.3] - 2026-03-18

### Added

- Windows desktop entry built on `pywebview`, so the app can run as a native desktop window
- reproducible PyInstaller build script for generating a distributable exe package
- local `settings.json` support for desktop builds, so packaged users can configure Kimi without editing environment variables

### Changed

- unified the product display name to `天枢智元·融谈Copilot`
- updated the health endpoint to return the app display name
- moved packaged-app data storage to a user-local writable directory when running from a frozen build

## [0.2.2] - 2026-03-18

### Added

- custom `All Rights Reserved` license file for public showcase without open-source usage rights
- Chinese license explainer for easier team review
- explicit commercial-use and permission guidance in the repository docs

### Changed

- bumped the public demo version to `0.2.2`
- clarified that the public GitHub repository is for showcase and evaluation, not unrestricted reuse

## [0.2.1] - 2026-03-18

### Added

- bilingual repository entry points with English and Simplified Chinese README files
- roadmap and contributing guides in both languages
- one-click launcher that installs dependencies, starts the server, waits for readiness, and opens the browser
- stop script for ending the local demo server cleanly
- optional `env.local.ps1` flow for machine-local Kimi and ASR settings

### Changed

- refreshed the GitHub homepage copy to feel more product-oriented and demo-friendly
- bumped the app version surfaced by the health endpoint to `0.2.1`
- optimized setup so dependency installation is skipped when requirements are already up to date

### Fixed

- reduced friction for colleagues trying the demo on a fresh Windows machine
- kept local machine settings out of git via `scripts/env.local.ps1`

## [0.2.0] - 2026-03-18

### Added

- Moonshot / Kimi integration through environment variables
- local `faster-whisper` transcription support
- audio upload workflow
- in-browser recording workflow
- transcript normalization via LLM when available
- colleague setup scripts and demo handoff docs
- public project files including roadmap, contribution guide, issue templates, and version tracking

### Changed

- upgraded the app from a transcript-only demo to an audio-capable internal trial build
- added app version exposure in the health endpoint
- clarified repository usage and contribution conventions for public collaboration

### Fixed

- improved Q&A extraction for freeform transcripts without explicit speaker labels
- reduced investor and founder role mix-ups by normalizing transcripts before analysis
- excluded generated share artifacts from git tracking

## [0.1.0] - 2026-03-18

### Added

- initial FastAPI MVP with dashboard and meeting analysis APIs
- transcript-driven meeting review flow
- topic library, canonical answers, and training script generation
- architecture and data pipeline documentation
- sample transcript and baseline API tests
