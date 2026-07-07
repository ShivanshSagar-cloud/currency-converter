from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from config import CACHE_FILE, HISTORY_FILE, MAX_HISTORY_ITEMS
from models.conversion import ConversionResult, ExchangeRateSnapshot


class CacheService:
    def __init__(self, cache_file: Path = CACHE_FILE, history_file: Path = HISTORY_FILE) -> None:
        self.cache_file = cache_file
        self.history_file = history_file

    def load_rate(self, from_currency: str, to_currency: str) -> ExchangeRateSnapshot | None:
        data = self._read_json(self.cache_file, default={})
        key = self._pair_key(from_currency, to_currency)
        snapshot = data.get("rates", {}).get(key)
        if not snapshot:
            return None

        return ExchangeRateSnapshot(
            base_currency=snapshot["base_currency"],
            quote_currency=snapshot["quote_currency"],
            rate=Decimal(snapshot["rate"]),
            fetched_at=datetime.fromisoformat(snapshot["fetched_at"]),
            source=snapshot["source"],
            is_live=bool(snapshot["is_live"]),
        )

    def save_rate(self, snapshot: ExchangeRateSnapshot) -> None:
        data = self._read_json(self.cache_file, default={"rates": {}, "updated_at": None})
        key = self._pair_key(snapshot.base_currency, snapshot.quote_currency)
        data.setdefault("rates", {})[key] = {
            "base_currency": snapshot.base_currency,
            "quote_currency": snapshot.quote_currency,
            "rate": str(snapshot.rate),
            "fetched_at": snapshot.fetched_at.isoformat(),
            "source": snapshot.source,
            "is_live": snapshot.is_live,
        }
        data["updated_at"] = datetime.now().isoformat()
        self._write_json(self.cache_file, data)

    def append_history(self, result: ConversionResult) -> None:
        history = self._read_json(self.history_file, default={"items": []})
        items = history.setdefault("items", [])
        items.insert(
            0,
            {
                "amount": str(result.amount),
                "from_currency": result.from_currency,
                "to_currency": result.to_currency,
                "exchange_rate": str(result.exchange_rate),
                "converted_amount": str(result.converted_amount),
                "timestamp": result.timestamp.isoformat(),
                "rate_source": result.rate_source,
                "is_live_rate": result.is_live_rate,
                "used_cached_rate": result.used_cached_rate,
            },
        )
        history["items"] = items[:MAX_HISTORY_ITEMS]
        self._write_json(self.history_file, history)

    def read_history(self) -> list[dict[str, Any]]:
        return self._read_json(self.history_file, default={"items": []}).get("items", [])

    def export_history_csv(self, destination: Path) -> Path:
        rows = self.read_history()
        header = [
            "timestamp",
            "amount",
            "from_currency",
            "to_currency",
            "exchange_rate",
            "converted_amount",
            "rate_source",
            "is_live_rate",
            "used_cached_rate",
        ]
        lines = [",".join(header)]
        for row in rows:
            lines.append(",".join(str(row.get(column, "")) for column in header))
        destination.write_text("\n".join(lines), encoding="utf-8")
        return destination

    def _pair_key(self, from_currency: str, to_currency: str) -> str:
        return f"{from_currency.upper()}_{to_currency.upper()}"

    def _read_json(self, path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return default

    def _write_json(self, path: Path, payload: Any) -> None:
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
