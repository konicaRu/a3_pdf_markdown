from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ConversionMetadata:
    method: str
    used_ocr: bool = False
    used_vision: bool = False

