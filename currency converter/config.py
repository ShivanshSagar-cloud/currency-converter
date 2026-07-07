from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "Real-Time Currency Converter"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Cursor"

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
DATA_DIR = BASE_DIR / "data"
EXPORTS_DIR = DATA_DIR / "exports"
LOGS_DIR = DATA_DIR / "logs"

CACHE_FILE = DATA_DIR / "rates_cache.json"
SETTINGS_FILE = DATA_DIR / "settings.json"
HISTORY_FILE = DATA_DIR / "history.json"
LOG_FILE = LOGS_DIR / "app.log"

API_BASE_URL = "https://api.exchangerate.host"
FALLBACK_API_BASE_URL = "https://api.frankfurter.dev/v1"
SYMBOLS_ENDPOINT = "/symbols"
LATEST_ENDPOINT = "/latest"
CONVERT_ENDPOINT = "/convert"
REQUEST_TIMEOUT = 12
CACHE_TTL_SECONDS = 60 * 15
EXCHANGERATE_HOST_ACCESS_KEY = os.getenv("EXCHANGERATE_HOST_ACCESS_KEY", "")
AUTO_REFRESH_INTERVAL_MS = 60 * 1000
MAX_HISTORY_ITEMS = 200

DEFAULT_BASE_CURRENCY = "USD"
DEFAULT_TARGET_CURRENCY = "INR"
DEFAULT_THEME = "dark"
DEFAULT_FAVORITES = ["USD", "EUR", "INR", "GBP", "JPY"]

WINDOW_MIN_WIDTH = 920
WINDOW_MIN_HEIGHT = 680
WINDOW_DEFAULT_WIDTH = 1120
WINDOW_DEFAULT_HEIGHT = 760

SUPPORTED_THEMES = {"light", "dark"}
DECIMAL_PLACES = "0.01"

for directory in (ASSETS_DIR, DATA_DIR, EXPORTS_DIR, LOGS_DIR):
    directory.mkdir(parents=True, exist_ok=True)
