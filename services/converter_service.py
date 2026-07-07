from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Callable

from api.exchange_service import ExchangeService
from config import EXPORTS_DIR
from models.conversion import ConversionRequest, ConversionResult
from models.currency import Currency
from services.cache_service import CacheService
from utils.formatters import build_terminal_output, quantize_money
from utils.validators import validate_currency


class ConverterService:
    def __init__(
        self,
        exchange_service: ExchangeService,
        cache_service: CacheService,
        printer: Callable[[str], None] | None = None,
    ) -> None:
        self.exchange_service = exchange_service
        self.cache_service = cache_service
        self.printer = printer or print
        self._currencies_cache: list[Currency] = []

    def load_currencies(self) -> list[Currency]:
        self._currencies_cache = self.exchange_service.fetch_symbols()
        return self._currencies_cache

    def available_currency_codes(self) -> set[str]:
        return {currency.code for currency in self._currencies_cache}

    def convert(self, request: ConversionRequest) -> ConversionResult:
        allowed_codes = self.available_currency_codes()
        if allowed_codes:
            from_currency = validate_currency(request.from_currency, allowed_codes)
            to_currency = validate_currency(request.to_currency, allowed_codes)
        else:
            from_currency = request.from_currency.upper()
            to_currency = request.to_currency.upper()

        snapshot = self.exchange_service.get_exchange_rate(from_currency, to_currency)
        converted_amount = quantize_money(request.amount * snapshot.rate)
        result = ConversionResult(
            amount=request.amount,
            from_currency=from_currency,
            to_currency=to_currency,
            exchange_rate=snapshot.rate,
            converted_amount=converted_amount,
            timestamp=datetime.now(),
            rate_source=snapshot.source,
            is_live_rate=snapshot.is_live,
            used_cached_rate=not snapshot.is_live,
        )
        self.cache_service.append_history(result)
        self.printer(build_terminal_output(result))
        return result

    def swap(self, from_currency: str, to_currency: str) -> tuple[str, str]:
        return to_currency, from_currency

    def get_history(self) -> list[dict[str, str]]:
        return self.cache_service.read_history()

    def export_history(self) -> str:
        destination = EXPORTS_DIR / f"conversion_history_{datetime.now():%Y%m%d_%H%M%S}.csv"
        return str(self.cache_service.export_history_csv(destination))
