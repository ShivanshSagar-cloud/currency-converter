from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal

import requests

from config import (
    API_BASE_URL,
    EXCHANGERATE_HOST_ACCESS_KEY,
    FALLBACK_API_BASE_URL,
    LATEST_ENDPOINT,
    REQUEST_TIMEOUT,
    SYMBOLS_ENDPOINT,
)
from models.conversion import ExchangeRateSnapshot
from models.currency import Currency
from services.cache_service import CacheService

LOGGER = logging.getLogger(__name__)


class ExchangeServiceError(Exception):
    pass


class ExchangeService:
    def __init__(self, cache_service: CacheService) -> None:
        self.cache_service = cache_service
        self.session = requests.Session()

    def fetch_symbols(self) -> list[Currency]:
        try:
            return self._fetch_symbols_exchangerate_host()
        except ExchangeServiceError as primary_error:
            LOGGER.warning("Primary symbol provider unavailable: %s", primary_error)
            try:
                return self._fetch_symbols_frankfurter()
            except requests.RequestException as error:
                raise ExchangeServiceError("Unable to load currency list from the exchange API.") from error

    def get_exchange_rate(self, from_currency: str, to_currency: str) -> ExchangeRateSnapshot:
        if from_currency == to_currency:
            return ExchangeRateSnapshot(
                base_currency=from_currency,
                quote_currency=to_currency,
                rate=Decimal("1"),
                fetched_at=datetime.now(),
                source="local",
                is_live=True,
            )

        cached = self.cache_service.load_rate(from_currency, to_currency)

        try:
            snapshot = self._fetch_rate_exchangerate_host(from_currency, to_currency)
            self.cache_service.save_rate(snapshot)
            return snapshot
        except (requests.RequestException, ValueError, ExchangeServiceError) as error:
            LOGGER.warning("Primary rate provider unavailable for %s/%s: %s", from_currency, to_currency, error)
            try:
                snapshot = self._fetch_rate_frankfurter(from_currency, to_currency)
                self.cache_service.save_rate(snapshot)
                return snapshot
            except (requests.RequestException, ValueError, ExchangeServiceError) as fallback_error:
                LOGGER.warning("Falling back to cache for %s/%s: %s", from_currency, to_currency, fallback_error)
            if cached:
                return ExchangeRateSnapshot(
                    base_currency=cached.base_currency,
                    quote_currency=cached.quote_currency,
                    rate=cached.rate,
                    fetched_at=cached.fetched_at,
                    source=f"{cached.source} (cached)",
                    is_live=False,
                )
            raise ExchangeServiceError(
                "Unable to fetch live exchange rates. Check your connection and try again."
            ) from error

    def _fetch_symbols_exchangerate_host(self) -> list[Currency]:
        params = {}
        if EXCHANGERATE_HOST_ACCESS_KEY:
            params["access_key"] = EXCHANGERATE_HOST_ACCESS_KEY

        response = self.session.get(
            f"{API_BASE_URL}{SYMBOLS_ENDPOINT}",
            params=params or None,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
        self._raise_for_api_error(payload)
        symbols = payload.get("symbols", {})
        return sorted(
            [Currency(code=code.upper(), name=details.get("description", code.upper())) for code, details in symbols.items()],
            key=lambda currency: currency.code,
        )

    def _fetch_symbols_frankfurter(self) -> list[Currency]:
        response = self.session.get(
            f"{FALLBACK_API_BASE_URL}/currencies",
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
        return sorted(
            [Currency(code=code.upper(), name=name) for code, name in payload.items()],
            key=lambda currency: currency.code,
        )

    def _fetch_rate_exchangerate_host(self, from_currency: str, to_currency: str) -> ExchangeRateSnapshot:
        params = {"base": from_currency, "symbols": to_currency}
        if EXCHANGERATE_HOST_ACCESS_KEY:
            params["access_key"] = EXCHANGERATE_HOST_ACCESS_KEY

        response = self.session.get(
            f"{API_BASE_URL}{LATEST_ENDPOINT}",
            params=params,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
        self._raise_for_api_error(payload)
        rates = payload.get("rates", {})
        rate_value = rates.get(to_currency)
        if rate_value is None:
            raise ExchangeServiceError(f"Exchange rate not available for {from_currency} to {to_currency}.")
        return ExchangeRateSnapshot(
            base_currency=from_currency,
            quote_currency=to_currency,
            rate=Decimal(str(rate_value)),
            fetched_at=datetime.now(),
            source="ExchangeRate.host",
            is_live=True,
        )

    def _fetch_rate_frankfurter(self, from_currency: str, to_currency: str) -> ExchangeRateSnapshot:
        response = self.session.get(
            f"{FALLBACK_API_BASE_URL}{LATEST_ENDPOINT}",
            params={"base": from_currency, "symbols": to_currency},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
        rates = payload.get("rates", {})
        rate_value = rates.get(to_currency)
        if rate_value is None:
            raise ExchangeServiceError(f"Exchange rate not available for {from_currency} to {to_currency}.")
        return ExchangeRateSnapshot(
            base_currency=from_currency,
            quote_currency=to_currency,
            rate=Decimal(str(rate_value)),
            fetched_at=datetime.now(),
            source="Frankfurter",
            is_live=True,
        )

    def _raise_for_api_error(self, payload: dict[str, object]) -> None:
        if payload.get("success", True):
            return
        error = payload.get("error", {})
        if isinstance(error, dict):
            message = str(error.get("info", "ExchangeRate.host request failed."))
        else:
            message = "ExchangeRate.host request failed."
        raise ExchangeServiceError(message)
