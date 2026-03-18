# Roadmap

[English](./ROADMAP.md) | [简体中文](./ROADMAP.zh-CN.md)

This roadmap keeps the project focused on the smallest set of features that can move it from a single-machine demo into a team-ready product.

## Product Goal

Build a system that helps fundraising teams:

- capture investor conversations
- evaluate answer quality
- preserve fundraising knowledge
- keep messaging consistent across team members

## v0.3.0 Internal Trial

Goal: make the product reliable enough for repeated internal use.

Planned work:

- async audio processing with visible progress states
- stronger role reconstruction for real-world transcripts
- exportable review summaries in Markdown or PDF
- better retry and failure handling in the workbench
- more structured scoring dimensions for fundraising answers

Success criteria:

- a 30 to 60 minute meeting can be uploaded without blocking the request lifecycle
- transcript reconstruction is stable enough for internal trial data
- a teammate can complete an end-to-end review without manual debugging

## v0.4.0 Team Rollout

Goal: move from local demo workflow to shared team usage.

Planned work:

- PostgreSQL plus `pgvector`
- multi-user workspace model
- approved canonical-answer workflow
- topic trend reporting
- stronger provider abstraction for LLM switching

Success criteria:

- multiple meetings can be searched and compared reliably
- approved scripts can be updated without editing raw JSON files
- the team can track message drift over time

## v0.5.0 Cross-Device Product

Goal: support real mobile and desktop product usage.

Planned work:

- Flutter clients for desktop and mobile
- object storage for meeting audio
- secure accounts and permission layers
- hosted deployment and environment management
- review queues and manager approval flow

Success criteria:

- users can record and review from both desktop and mobile devices
- recordings and reviews are no longer tied to one local machine
- the product is ready for a managed pilot

## Out of Scope for Now

- CRM integrations
- investor outreach automation
- production-grade access control
- multilingual transcript correction workflows
