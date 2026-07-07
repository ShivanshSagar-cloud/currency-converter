from __future__ import annotations

import argparse
import logging
from decimal import Decimal

from api.exchange_service import ExchangeService
from gui.app import CurrencyConverterApp
from models.conversion import ConversionRequest
from services.cache_service import CacheService
from services.converter_service import ConverterService
from services.settings_service import SettingsService
from utils.logger import setup_logging


LOGGER = logging.getLogger(__name__)


def build_services() -> tuple[ConverterService, SettingsService]:
    cache_service = CacheService()
    settings_service = SettingsService()
    exchange_service = ExchangeService(cache_service)
    converter_service = ConverterService(exchange_service=exchange_service, cache_service=cache_service)
    return converter_service, settings_service


def run_cli(converter_service: ConverterService, amount: str, from_currency: str, to_currency: str) -> None:
    converter_service.load_currencies()
    converter_service.convert(
        ConversionRequest(
            amount=Decimal(amount),
            from_currency=from_currency,
            to_currency=to_currency,
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Real-Time Currency Converter")
    parser.add_argument("--cli-only", action="store_true", help="Run a terminal conversion without launching the GUI.")
    parser.add_argument("--amount", default="100", help="Amount to convert in CLI mode.")
    parser.add_argument("--from-currency", default="USD", help="Source currency code for CLI mode.")
    parser.add_argument("--to-currency", default="INR", help="Target currency code for CLI mode.")
    return parser.parse_args()


def main() -> None:
    setup_logging()
    args = parse_args()
    converter_service, settings_service = build_services()

    if args.cli_only:
        run_cli(converter_service, args.amount, args.from_currency, args.to_currency)
        return

    app = CurrencyConverterApp(converter_service=converter_service, settings_service=settings_service)
    app.mainloop()


if __name__ == "__main__":
    main()
