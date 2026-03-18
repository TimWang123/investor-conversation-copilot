# Changelog

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
