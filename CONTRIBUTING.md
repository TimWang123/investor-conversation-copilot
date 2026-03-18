# Contributing

Thanks for contributing to `Investor Conversation Copilot`.

## Development Setup

1. Create a virtual environment.
2. Install dependencies from `requirements.txt`.
3. Start the app locally with:

```powershell
.\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

4. Run tests before opening a pull request:

```powershell
.\.venv\Scripts\python -m pytest -q
```

## Contribution Rules

- Do not commit secrets, tokens, or local environment files.
- Add or update tests for any behavior change that can be validated automatically.
- Update `CHANGELOG.md` for user-visible features, fixes, or behavior changes.
- Keep the demo path working: transcript input, audio upload, and dashboard review should remain functional.
- Prefer small, reviewable pull requests.

## Pull Request Checklist

- explain what changed
- explain why it changed
- list how it was tested
- include screenshots when the UI changed
- mention any roadmap impact or follow-up work

## Release Notes

- `VERSION` tracks the current demo release number
- `CHANGELOG.md` tracks user-visible release history
- `ROADMAP.md` tracks planned next steps

