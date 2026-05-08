from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from PIL import Image, UnidentifiedImageError

from a3_pdf_markdown.app.converters.vision_client import VisionClient, build_vision_client
from a3_pdf_markdown.app.core.models import AppConfig, LogLevel


PPTX_IMAGE_PROMPT = (
    "Опиши изображение из презентации по-русски. Если это график или диаграмма, "
    "укажи тип, подписи, видимые значения и ключевой вывод. Если это схема, "
    "перечисли блоки и связи. Если это обычная иллюстрация, кратко опиши смысл. "
    "Не пересказывай весь слайд и не добавляй вводных фраз."
)


@dataclass(slots=True)
class PptxImageDescription:
    slide_number: int
    image_number: int
    description: str


class PptxEnricher:
    def __init__(self, config: AppConfig, log: Callable[[LogLevel, str], None]) -> None:
        self.config = config
        self.log = log
        self._vision: VisionClient | None = None

    def describe_images(self, source_path: Path) -> list[PptxImageDescription]:
        if not self.config.vision_enabled:
            return []

        try:
            from pptx import Presentation
            from pptx.enum.shapes import MSO_SHAPE_TYPE
        except ImportError:
            self.log(LogLevel.WARNING, "Для описания картинок PPTX нужен пакет python-pptx")
            return []

        presentation = Presentation(str(source_path))
        descriptions: list[PptxImageDescription] = []

        for slide_index, slide in enumerate(presentation.slides, start=1):
            image_index = 0
            for shape in slide.shapes:
                if shape.shape_type != MSO_SHAPE_TYPE.PICTURE:
                    continue

                image_index += 1
                try:
                    image = Image.open(io.BytesIO(shape.image.blob))
                    self.log(
                        LogLevel.INFO,
                        f"PPTX слайд {slide_index}: описание изображения {image_index}",
                    )
                    description = self._vision_client().describe_image(image, PPTX_IMAGE_PROMPT)
                except (UnidentifiedImageError, OSError) as exc:
                    description = f"Не удалось прочитать изображение: {exc}"
                except Exception as exc:
                    description = f"Vision не смог описать изображение: {exc}"

                if description.strip():
                    descriptions.append(
                        PptxImageDescription(
                            slide_number=slide_index,
                            image_number=image_index,
                            description=description.strip(),
                        )
                    )

        return descriptions

    def append_descriptions(self, markdown: str, source_path: Path) -> tuple[str, bool]:
        descriptions = self.describe_images(source_path)
        if not descriptions:
            return markdown, False

        parts = [markdown.rstrip(), "\n\n## Описания изображений\n"]
        for item in descriptions:
            parts.append(
                f"\n### Слайд {item.slide_number}, изображение {item.image_number}\n\n"
                f"{item.description}\n"
            )
        return "".join(parts).strip() + "\n", True

    def _vision_client(self) -> VisionClient:
        if self._vision is None:
            self._vision = build_vision_client(self.config)
        return self._vision

