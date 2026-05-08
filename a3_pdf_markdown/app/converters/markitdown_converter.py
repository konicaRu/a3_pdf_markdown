from __future__ import annotations

from pathlib import Path
from typing import Callable, Protocol

from a3_pdf_markdown.app.converters.base import ConversionMetadata
from a3_pdf_markdown.app.converters.pdf_pipeline import PdfPipeline
from a3_pdf_markdown.app.converters.vision_client import OpenAICompatibleVisionClient
from a3_pdf_markdown.app.core.models import AppConfig, LogLevel, VisionProvider


class CancellationToken(Protocol):
    cancelled: bool


class DocumentConverterService:
    def __init__(self, config: AppConfig, log: Callable[[LogLevel, str], None]) -> None:
        self.config = config
        self.log = log
        self.pdf_pipeline = PdfPipeline(config, log)
        self._markitdown = None

    def convert(self, source_path: Path, cancellation: CancellationToken) -> tuple[str, ConversionMetadata]:
        if source_path.suffix.lower() == ".pdf":
            return self.pdf_pipeline.convert(source_path, cancellation)

        converter = self._markitdown_converter()
        result = converter.convert(str(source_path))
        text = getattr(result, "text_content", "")
        return text, ConversionMetadata(
            method="MarkItDown",
            used_ocr=False,
            used_vision=self.config.vision_enabled,
        )

    def _markitdown_converter(self):
        if self._markitdown is not None:
            return self._markitdown

        try:
            from markitdown import MarkItDown
        except ImportError as exc:
            raise RuntimeError("Для конвертации нужен пакет markitdown[all]") from exc

        if self.config.vision_enabled and self.config.vision_provider == VisionProvider.LM_STUDIO:
            try:
                vision = OpenAICompatibleVisionClient(
                    self.config.vision_base_url,
                    self.config.vision_model,
                )
                self._markitdown = MarkItDown(
                    llm_client=vision.client,
                    llm_model=self.config.vision_model,
                    llm_prompt=(
                        "Кратко опиши изображение по-русски. Для графиков и схем укажи "
                        "структуру, подписи и ключевые выводы. Не добавляй вводных фраз."
                    ),
                )
                return self._markitdown
            except Exception as exc:
                self.log(LogLevel.WARNING, f"MarkItDown запущен без LLM: {exc}")

        self._markitdown = MarkItDown()
        return self._markitdown
