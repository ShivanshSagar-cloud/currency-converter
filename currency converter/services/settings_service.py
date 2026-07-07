from __future__ import annotations

import json
from pathlib import Path

from config import SETTINGS_FILE, SUPPORTED_THEMES
from models.settings import AppSettings


class SettingsService:
    def __init__(self, settings_file: Path = SETTINGS_FILE) -> None:
        self.settings_file = settings_file

    def load(self) -> AppSettings:
        defaults = AppSettings()
        if not self.settings_file.exists():
            settings = defaults
            self.save(settings)
            return settings

        try:
            payload = json.loads(self.settings_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            settings = defaults
            self.save(settings)
            return settings

        theme = payload.get("theme", defaults.theme)
        if theme not in SUPPORTED_THEMES:
            theme = defaults.theme

        return AppSettings(
            theme=theme,
            auto_refresh_enabled=bool(payload.get("auto_refresh_enabled", True)),
            auto_refresh_seconds=max(15, int(payload.get("auto_refresh_seconds", 60))),
            favorite_currencies=list(payload.get("favorite_currencies", defaults.favorite_currencies)),
            default_from_currency=payload.get("default_from_currency", defaults.default_from_currency),
            default_to_currency=payload.get("default_to_currency", defaults.default_to_currency),
        )

    def save(self, settings: AppSettings) -> None:
        payload = {
            "theme": settings.theme,
            "auto_refresh_enabled": settings.auto_refresh_enabled,
            "auto_refresh_seconds": settings.auto_refresh_seconds,
            "favorite_currencies": settings.favorite_currencies,
            "default_from_currency": settings.default_from_currency,
            "default_to_currency": settings.default_to_currency,
        }
        self.settings_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
