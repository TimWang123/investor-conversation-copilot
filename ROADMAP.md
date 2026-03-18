# Roadmap

This roadmap keeps the project focused on the smallest set of features that can turn the demo into a real internal product.

## Product Goal

Build a system that helps founders and fundraising teams:

- capture investor conversations
- evaluate answer quality
- preserve institutional fundraising knowledge
- keep team messaging consistent over time

## Next Stage: v0.3.0 Internal Trial

Target: make the product reliable enough for repeated internal use.

Planned work:

- async audio processing with progress states
- stronger speaker-role reconstruction for real-world transcripts
- exportable review summaries in Markdown or PDF
- better error states and retry UX in the web workbench
- more structured scoring dimensions for fundraising answers

Exit criteria:

- a 30 to 60 minute meeting can be uploaded without blocking the request lifecycle
- transcript reconstruction is stable enough for internal demo data
- a teammate can run the project locally and finish one end-to-end review without manual debugging

## Stage After That: v0.4.0 Team Rollout

Target: move from local demo workflow to shared team usage.

Planned work:

- PostgreSQL plus `pgvector` storage
- multi-user team workspace model
- approved canonical answer workflow
- trend reporting across recurring investor topics
- stronger model abstraction for swapping providers

Exit criteria:

- multiple meetings can be searched and compared reliably
- approved training scripts can be updated without editing raw JSON files
- the team can see topic drift and answer consistency over time

## Longer-Term: v0.5.0 Cross-Device Product

Target: support real mobile and desktop product usage.

Planned work:

- Flutter client for desktop and mobile
- object storage for meeting audio
- secure account and permission model
- hosted deployment and environment management
- review queues and manager approval workflow

Exit criteria:

- users can record and review from mobile and desktop devices
- recordings and meeting reviews are stored outside local files
- the product is ready for a managed pilot instead of a single-machine demo

## Out of Scope for Now

- CRM integrations
- investor outreach automation
- production-grade access control
- multilingual transcript correction workflows

