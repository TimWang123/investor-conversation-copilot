from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BASE_DIR / "app"
STATIC_DIR = APP_DIR / "static"
SAMPLES_DIR = BASE_DIR / "samples"
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

STATE_FILE = Path(os.getenv("COPILOT_STATE_FILE", DATA_DIR / "app_state.json"))

