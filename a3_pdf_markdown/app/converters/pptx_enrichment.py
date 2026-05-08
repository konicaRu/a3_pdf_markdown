from __future__ import annotations

import io
import re
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


SLIDE_MARKER_RE = re.compile(r"(<!--\s*Slide number:\s*(\d+)\s*-->)")
IMAGE_MARKDOWN_RE = re.compile(r"(!\[[^\]]*]\([^)]+\))")


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
                    self.log(
                        LogLevel.WARNING,
                        f"PPTX слайд {slide_index}, изображение {image_index}: "
                        f"не удалось прочитать изображение: {exc}",
                    )
                    continue
                except Exception as exc:
                    self.log(
                        LogLevel.WARNING,
                        f"PPTX слайд {slide_index}, изображение {image_index}: "
                        f"vision не смог описать изображение: {exc}",
                    )
                    continue

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

        by_slide: dict[int, list[PptxImageDescription]] = {}
        for item in descriptions:
            by_slide.setdefault(item.slide_number, []).append(item)

        split = SLIDE_MARKER_RE.split(markdown)
        if len(split) == 1:
            return self._append_fallback(markdown, descriptions), True

        result = [split[0]]
        inserted_any = False
        for index in range(1, len(split), 3):
            marker = split[index]
            slide_number = int(split[index + 1])
            slide_body = split[index + 2]
            enriched_body, inserted = self._insert_into_slide(
                slide_body,
                by_slide.get(slide_number, []),
            )
            inserted_any = inserted_any or inserted
            result.extend([marker, enriched_body])

        if not inserted_any:
            return self._append_fallback(markdown, descriptions), True
        return "".join(result).strip() + "\n", True

    def _insert_into_slide(
        self,
        slide_body: str,
        descriptions: list[PptxImageDescription],
    ) -> tuple[str, bool]:
        if not descriptions:
            return slide_body, False

        by_image = {item.image_number: item for item in descriptions}
        image_counter = 0
        inserted = False

        def replace(match: re.Match[str]) -> str:
            nonlocal image_counter, inserted
            image_counter += 1
            item = by_image.get(image_counter)
            if item is None:
                return match.group(0)
            inserted = True
            return (
                f"{match.group(0)}\n\n"
                f"> **Описание изображения:** {item.description}\n"
            )

        enriched = IMAGE_MARKDOWN_RE.sub(replace, slide_body)
        missing = [item for item in descriptions if item.image_number > image_counter]
        if missing:
            inserted = True
            extra = ["\n\n### Описания изображений слайда\n"]
            for item in missing:
                extra.append(f"\n- Изображение {item.image_number}: {item.description}")
            enriched = enriched.rstrip() + "".join(extra) + "\n"
        return enriched, inserted

    def _append_fallback(
        self,
        markdown: str,
        descriptions: list[PptxImageDescription],
    ) -> str:
        parts = [markdown.rstrip(), "\n\n## Описания изображений\n"]
        for item in descriptions:
            parts.append(
                f"\n### Слайд {item.slide_number}, изображение {item.image_number}\n\n"
                f"{item.description}\n"
            )
        return "".join(parts).strip() + "\n"

    def _vision_client(self) -> VisionClient:
        if self._vision is None:
            self._vision = build_vision_client(self.config)
        return self._vision
