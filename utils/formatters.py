from __future__ import annotations

from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from config import DECIMAL_PLACES
from models.conversion import ConversionResult

CURRENCY_SYMBOLS = {
    "AED": "AED ",
    "AUD": "A$",
    "CAD": "C$",
    "CHF": "CHF ",
    "CNY": "CNY ",
    "EUR": "EUR ",
    "GBP": "GBP ",
    "INR": "₹",
    "JPY": "¥",
    "SGD": "S$",
    "USD": "$",
}


def quantize_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal(DECIMAL_PLACES), rounding=ROUND_HALF_UP)


def format_money(value: Decimal, currency_code: str) -> str:
    symbol = CURRENCY_SYMBOLS.get(currency_code.upper(), f"{currency_code.upper()} ")
    amount = quantize_money(value)
    return f"{symbol}{amount:,.2f}"


def format_timestamp(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S")


def build_terminal_output(result: ConversionResult) -> str:
    amount_display = f"{quantize_money(result.amount):,.2f}"
    return "\n".join(
        [
            "-" * 36,
            "Currency Converter",
            "-" * 36,
            "",
            "Amount:",
            amount_display,
            "",
            "From:",
            result.from_currency,
            "",
            "To:",
            result.to_currency,
            "",
            "Exchange Rate:",
            f"1 {result.from_currency} = {quantize_money(result.exchange_rate):,.4f} {result.to_currency}",
            "",
            "Converted Amount:",
            format_money(result.converted_amount, result.to_currency),
            "",
            "Time:",
            format_timestamp(result.timestamp),
            "-" * 36,
        ]
    )
