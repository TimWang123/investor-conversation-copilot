from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BASE_DIR / "app"
STATIC_DIR = APP_DIR / "static"
SAMPLES_DIR = BASE_DIR / "samples"
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
UPLOADS_DIR = DATA_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)
MODELS_DIR = DATA_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

STATE_FILE = Path(os.getenv("COPILOT_STATE_FILE", DATA_DIR / "app_state.json"))
APP_VERSION = os.getenv("APP_VERSION", "0.2.0").strip() or "0.2.0"

MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY", "").strip()
MOONSHOT_BASE_URL = os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.cn/v1").rstrip("/")
MOONSHOT_MODEL = os.getenv("MOONSHOT_MODEL", "kimi-latest").strip()

ASR_MODEL_SIZE = os.getenv("ASR_MODEL_SIZE", "small").strip()
ASR_DEVICE = os.getenv("ASR_DEVICE", "cpu").strip()
ASR_COMPUTE_TYPE = os.getenv("ASR_COMPUTE_TYPE", "int8").strip()
