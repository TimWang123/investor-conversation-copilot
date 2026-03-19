from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _resource_base_dir() -> Path:
    if getattr(sys, "frozen", False) and getattr(sys, "_MEIPASS", None):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def _install_dir(resource_dir: Path) -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return resource_dir


BASE_DIR = _resource_base_dir()
INSTALL_DIR = _install_dir(BASE_DIR)
APP_DIR = BASE_DIR / "app"
STATIC_DIR = APP_DIR / "static"
SAMPLES_DIR = BASE_DIR / "samples"


def _default_data_dir() -> Path:
    custom_home = os.getenv("COPILOT_HOME", "").strip()
    if custom_home:
        return Path(custom_home).expanduser()
    if getattr(sys, "frozen", False):
        local_appdata = os.getenv("LOCALAPPDATA", "").strip()
        if local_appdata:
            return Path(local_appdata) / "TianshuZhiyuan" / "RongtanCopilot"
        return Path.home() / "AppData" / "Local" / "TianshuZhiyuan" / "RongtanCopilot"
    return BASE_DIR / "data"


DATA_DIR = _default_data_dir()
DATA_DIR.mkdir(exist_ok=True)
UPLOADS_DIR = DATA_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)
MODELS_DIR = DATA_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

STATE_FILE = Path(os.getenv("COPILOT_STATE_FILE", DATA_DIR / "app_state.json"))
VERSION_FILE = BASE_DIR / "VERSION"


def _load_default_app_version() -> str:
    if VERSION_FILE.exists():
        version = VERSION_FILE.read_text(encoding="utf-8").strip()
        if version:
            return version
    return "0.2.3"


def _candidate_settings_files() -> list[Path]:
    custom_settings = os.getenv("COPILOT_SETTINGS_FILE", "").strip()
    if custom_settings:
        return [Path(custom_settings).expanduser()]

    candidates = [INSTALL_DIR / "settings.json"]
    data_settings = DATA_DIR / "settings.json"
    if data_settings not in candidates:
        candidates.append(data_settings)
    return candidates


def _load_local_settings() -> dict[str, object]:
    for candidate in _candidate_settings_files():
        if not candidate.exists():
            continue
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        if isinstance(payload, dict):
            return payload
    return {}


def _read_setting(name: str, default: str) -> str:
    env_value = os.getenv(name, "").strip()
    if env_value:
        return env_value
    local_value = LOCAL_SETTINGS.get(name, default)
    return str(local_value).strip() or default


APP_VERSION = os.getenv("APP_VERSION", _load_default_app_version()).strip() or _load_default_app_version()
APP_DISPLAY_NAME = os.getenv("APP_DISPLAY_NAME", "天枢智元·融谈Copilot").strip() or "天枢智元·融谈Copilot"
LOCAL_SETTINGS = _load_local_settings()

MOONSHOT_API_KEY = _read_setting("MOONSHOT_API_KEY", "")
MOONSHOT_BASE_URL = _read_setting("MOONSHOT_BASE_URL", "https://api.moonshot.cn/v1").rstrip("/")
MOONSHOT_MODEL = _read_setting("MOONSHOT_MODEL", "kimi-latest")

ASR_MODEL_SIZE = _read_setting("ASR_MODEL_SIZE", "small")
ASR_DEVICE = _read_setting("ASR_DEVICE", "cpu")
ASR_COMPUTE_TYPE = _read_setting("ASR_COMPUTE_TYPE", "int8")
