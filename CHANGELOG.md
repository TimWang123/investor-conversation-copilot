# Changelog

This project follows a simple changelog discipline:

- every user-visible feature change should be added here
- every public release should have a version section
- every breaking or notable behavior change should be called out explicitly

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
- reduced investor/founder role mix-ups by normalizing transcripts before analysis
- excluded generated share artifacts from git tracking

## [0.1.0] - 2026-03-18

### Added

- initial FastAPI MVP with dashboard and meeting analysis APIs
- transcript-driven meeting review flow
- topic library, canonical answers, and training script generation
- architecture and data pipeline documentation
- sample transcript and baseline API tests

