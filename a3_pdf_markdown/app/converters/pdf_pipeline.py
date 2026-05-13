from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol

from PIL import Image

from a3_pdf_markdown.app.converters.base import ConversionMetadata
from a3_pdf_markdown.app.converters.ocr_engine import EasyOcrEngine
from a3_pdf_markdown.app.converters.vision_client import VisionClient, build_vision_client
from a3_pdf_markdown.app.core.models import AppConfig, LogLevel


class CancellationToken(Protocol):
    cancelled: bool


VISION_PROMPT = (
    "Опиши только визуально значимые элементы страницы: графики, схемы, диаграммы, "
    "важные изображения и таблицы, если они видны как картинка. Не пересказывай весь "
    "документ. Если видишь таблицу, верни ее как Markdown-таблицу. Если это схема, "
    "кратко перечисли блоки и связи. Пиши по-русски, без вводных фраз."
)


@dataclass(slots=True)
class PdfPageResult:
    markdown: str
    used_ocr: bool = False
    used_vision: bool = False


class PdfPipeline:
    def __init__(self, config: AppConfig, log: Callable[[LogLevel, str], None]) -> None:
        self.config = config
        self.log = log
        self._ocr: EasyOcrEngine | None = None
        self._vision: VisionClient | None = None

    def convert(self, source_path: Path, cancellation: CancellationToken) -> tuple[str, ConversionMetadata]:
        try:
            import fitz
        except ImportError as exc:
            raise RuntimeError("Для обработки PDF нужен пакет pymupdf") from exc

        fitz.TOOLS.mupdf_display_errors(False)
        doc = fitz.open(source_path)
        parts: list[str] = []
        used_ocr = False
        used_vision = False

        try:
            for page_index, page in enumerate(doc, start=1):
                if cancellation.cancelled:
                    break
                result = self._convert_page(page, page_index, len(doc))
                parts.append(result.markdown)
                used_ocr = used_ocr or result.used_ocr
                used_vision = used_vision or result.used_vision
        finally:
            doc.close()

        return "\n\n---\n\n".join(parts), ConversionMetadata(
            method="PDF",
            used_ocr=used_ocr,
            used_vision=used_vision,
        )

    def _convert_page(self, page, page_index: int, total_pages: int) -> PdfPageResult:
        self.log(LogLevel.INFO, f"PDF страница {page_index}/{total_pages}")

        used_ocr = False
        used_vision = False

        # Сначала пробуем структурное извлечение таблиц
        tables_md, table_bboxes = self._extract_tables(page)
        if tables_md:
            self.log(LogLevel.INFO, f"Страница {page_index}: найдено таблиц: {len(tables_md)}")
            non_table_text = self._extract_text_outside_tables(page, table_bboxes)
            page_parts = [f"## Страница {page_index}"]
            if non_table_text.strip():
                page_parts.append(non_table_text.strip())
            page_parts.extend(tables_md)
            return PdfPageResult("\n\n".join(page_parts), used_ocr, used_vision)

        # Таблиц нет — текстовый слой + OCR fallback
        text = self._extract_text_layer(page)

        if len(text) < self.config.min_text_chars_per_page and self.config.ocr_enabled:
            image = self._render_page(page)
            self.log(LogLevel.INFO, f"Страница {page_index}: слабый текстовый слой, запускаю OCR")
            ocr_result = self._ocr_engine().read_image(image)
            if len(ocr_result.text) > len(text):
                text = ocr_result.text
            used_ocr = True

        visual_note = ""
        needs_vision = self._page_has_visuals(page) or len(text) < self.config.min_text_chars_per_page
        if self.config.vision_enabled and needs_vision:
            try:
                image = self._render_page(page)
                self.log(LogLevel.INFO, f"Страница {page_index}: анализ визуальных элементов")
                visual_note = self._vision_client().describe_image(image, VISION_PROMPT)
                used_vision = bool(visual_note.strip())
            except Exception as exc:
                self.log(LogLevel.WARNING, f"Vision не сработал на странице {page_index}: {exc}")

        page_parts = [f"## Страница {page_index}"]
        if text.strip():
            page_parts.append(text.strip())
        else:
            page_parts.append("> Текст не распознан.")
        if visual_note.strip():
            page_parts.append("### Визуальные элементы\n\n" + visual_note.strip())

        return PdfPageResult("\n\n".join(page_parts), used_ocr, used_vision)

    def _extract_tables(self, page) -> tuple[list[str], list[tuple[float, float, float, float]]]:
        """Извлекает таблицы через PyMuPDF и возвращает (список MD-таблиц, список bbox)."""
        try:
            finder = page.find_tables()
            if not finder.tables:
                return [], []
            tables_md = []
            bboxes = []
            for table in finder.tables:
                rows = table.extract()
                if not rows:
                    continue
                md = self._rows_to_markdown(rows)
                if md:
                    tables_md.append(md)
                    r = table.bbox
                    bboxes.append((r[0], r[1], r[2], r[3]))
            return tables_md, bboxes
        except Exception as exc:
            self.log(LogLevel.WARNING, f"Ошибка при поиске таблиц: {exc}")
            return [], []

    def _rows_to_markdown(self, rows: list[list]) -> str:
        if not rows:
            return ""

        def cell(v: object) -> str:
            return str(v).replace("\n", " ").replace("|", "\\|").strip() if v is not None else ""

        header = rows[0]
        lines = ["| " + " | ".join(cell(c) for c in header) + " |"]
        lines.append("| " + " | ".join("---" for _ in header) + " |")
        for row in rows[1:]:
            lines.append("| " + " | ".join(cell(c) for c in row) + " |")
        return "\n".join(lines)

    def _extract_text_outside_tables(
        self, page, table_bboxes: list[tuple[float, float, float, float]]
    ) -> str:
        blocks = page.get_text("blocks") or []
        lines = []
        for block in blocks:
            if block[6] != 0:
                continue
            bx0, by0, bx1, by1 = block[:4]
            inside_table = any(
                min(bx1, tx1) > max(bx0, tx0) and min(by1, ty1) > max(by0, ty0)
                for tx0, ty0, tx1, ty1 in table_bboxes
            )
            if not inside_table:
                text = block[4].strip()
                if text:
                    lines.append(text)
        return "\n".join(lines)

    def _extract_text_layer(self, page) -> str:
        text = page.get_text("text") or ""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    def _page_has_visuals(self, page) -> bool:
        try:
            if page.get_images(full=True):
                return True
            drawings = page.get_drawings()
            return len(drawings) >= 8
        except Exception:
            return False

    def _render_page(self, page) -> Image.Image:
        import fitz

        zoom = self.config.pdf_render_dpi / 72
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        return Image.open(io.BytesIO(pix.tobytes("png")))

    def _ocr_engine(self) -> EasyOcrEngine:
        if self._ocr is None:
            self.log(LogLevel.INFO, "Инициализация EasyOCR")
            self._ocr = EasyOcrEngine(["ru", "en"], gpu=False)
        return self._ocr

    def _vision_client(self) -> VisionClient:
        if self._vision is None:
            self.log(LogLevel.INFO, "Инициализация vision-клиента")
            self._vision = build_vision_client(self.config)
        return self._vision
