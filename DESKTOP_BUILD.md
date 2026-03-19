# Desktop Build Guide

This project can be packaged into a Windows desktop app named `天枢智元·融谈Copilot`.

## What It Builds

The desktop build is a native Windows executable that:

- starts the local FastAPI service in the background
- opens the product in a desktop window via `pywebview`
- stores user data in a writable local directory for packaged builds

## Build Steps

1. Create or reuse the project virtual environment.
2. Install desktop build dependencies:

```powershell
.\.venv\Scripts\python -m pip install -r requirements-desktop.txt
```

3. Run the build script:

```powershell
.\scripts\build-desktop.ps1 -Clean
```

4. Find the result in:

```text
dist\天枢智元-融谈Copilot
```

## Files to Share

Share the whole output folder, not only the exe.

Important files:

- `天枢智元-融谈Copilot.exe`
- `settings.example.json`
- any files created by PyInstaller inside the output folder

## Kimi Configuration for Packaged App

For the desktop package, the easiest configuration path is:

1. Copy `settings.example.json` to `settings.json`
2. Fill in the Moonshot / Kimi values
3. Keep `settings.json` next to the exe

Example:

```json
{
  "MOONSHOT_API_KEY": "replace-with-your-key",
  "MOONSHOT_BASE_URL": "https://api.moonshot.cn/v1",
  "MOONSHOT_MODEL": "kimi-latest",
  "ASR_MODEL_SIZE": "small",
  "ASR_DEVICE": "cpu",
  "ASR_COMPUTE_TYPE": "int8"
}
```

## Notes

- the first audio transcription may download the local whisper model
- packaged builds use a local writable data directory instead of writing into the app bundle
- if port `8000` is occupied, the desktop app automatically looks for another local port
