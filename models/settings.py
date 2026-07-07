from __future__ import annotations

from dataclasses import dataclass, field

from config import DEFAULT_BASE_CURRENCY, DEFAULT_FAVORITES, DEFAULT_TARGET_CURRENCY, DEFAULT_THEME


@dataclass(slots=True)
class AppSettings:
    theme: str = DEFAULT_THEME
    auto_refresh_enabled: bool = True
    auto_refresh_seconds: int = 60
    favorite_currencies: list[str] = field(default_factory=lambda: list(DEFAULT_FAVORITES))
    default_from_currency: str = DEFAULT_BASE_CURRENCY
    default_to_currency: str = DEFAULT_TARGET_CURRENCY
