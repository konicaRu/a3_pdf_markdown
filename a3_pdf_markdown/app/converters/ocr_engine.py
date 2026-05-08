from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image


@dataclass(slots=True)
class OcrResult:
    text: str
    line_count: int


class EasyOcrEngine:
    def __init__(self, languages: list[str] | None = None, gpu: bool = False) -> None:
        import easyocr

        self.reader = easyocr.Reader(languages or ["ru", "en"], gpu=gpu)

    def read_image(self, image: Image.Image) -> OcrResult:
        lines = self.reader.readtext(np.array(image), detail=0)
        text_lines = [str(line).strip() for line in lines if str(line).strip()]
        return OcrResult(text="\n".join(text_lines), line_count=len(text_lines))

