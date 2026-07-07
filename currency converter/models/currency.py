from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class Currency:
    code: str
    name: str

    @property
    def display_name(self) -> str:
        return f"{self.code} - {self.name}"
