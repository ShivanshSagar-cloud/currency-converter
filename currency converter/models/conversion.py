from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


@dataclass(slots=True)
class ConversionRequest:
    amount: Decimal
    from_currency: str
    to_currency: str


@dataclass(slots=True)
class ExchangeRateSnapshot:
    base_currency: str
    quote_currency: str
    rate: Decimal
    fetched_at: datetime
    source: str
    is_live: bool


@dataclass(slots=True)
class ConversionResult:
    amount: Decimal
    from_currency: str
    to_currency: str
    exchange_rate: Decimal
    converted_amount: Decimal
    timestamp: datetime
    rate_source: str
    is_live_rate: bool
    message: str = ""
    used_cached_rate: bool = False
    metadata: dict[str, str] = field(default_factory=dict)
