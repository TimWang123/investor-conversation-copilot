# Contributing

[English](./CONTRIBUTING.md) | [简体中文](./CONTRIBUTING.zh-CN.md)

Thanks for contributing to `Investor Conversation Copilot`.

## Local Setup

1. Create a virtual environment.
2. Install dependencies from `requirements.txt`.
3. Start the app locally:

```powershell
.\scripts\run-demo.ps1
```

4. Run tests before opening a pull request:

```powershell
.\.venv\Scripts\python -m pytest -q
```

## Contribution Rules

- Never commit secrets, tokens, or machine-local env files
- Add or update tests for behavior changes that can be automated
- Update `CHANGELOG.md` for user-visible changes
- Keep the main demo path working: transcript input, audio upload, and review output
- Prefer small pull requests with clear scope

## Pull Request Checklist

- explain what changed
- explain why it changed
- list how it was tested
- include screenshots when the UI changed
- mention follow-up work if the feature is incomplete

## Release Files

- `VERSION` stores the current public demo version
- `CHANGELOG.md` stores release history
- `ROADMAP.md` stores planned milestones
