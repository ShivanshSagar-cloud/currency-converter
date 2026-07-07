from __future__ import annotations

from decimal import Decimal, InvalidOperation


def parse_amount(raw_value: str) -> Decimal:
    value = raw_value.strip()
    if not value:
        raise ValueError("Please enter an amount.")

    try:
        amount = Decimal(value)
    except InvalidOperation as error:
        raise ValueError("Amount must be a valid number.") from error

    if amount <= Decimal("0"):
        raise ValueError("Amount must be greater than zero.")

    return amount


def validate_currency(code: str, allowed: set[str]) -> str:
    normalized = code.strip().upper()
    if not normalized:
        raise ValueError("Please choose a currency.")
    if normalized not in allowed:
        raise ValueError(f"Unsupported currency: {normalized}")
    return normalized
