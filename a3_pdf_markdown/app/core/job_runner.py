from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import monotonic, strftime
from typing import Callable

from a3_pdf_markdown.app.converters.markitdown_converter import DocumentConverterService
from a3_pdf_markdown.app.core.models import (
    AppConfig,
    FileResult,
    LogEvent,
    LogLevel,
    ProgressEvent,
    RunStats,
)
from a3_pdf_markdown.app.core.paths import collect_input_files, unique_output_path


@dataclass(slots=True)
class CancellationToken:
    cancelled: bool = False

    def cancel(self) -> None:
        self.cancelled = True


class JobRunner:
    def __init__(
        self,
        config: AppConfig,
        on_log: Callable[[LogEvent], None],
        on_progress: Callable[[ProgressEvent], None],
        on_result: Callable[[FileResult], None],
        cancellation: CancellationToken,
    ) -> None:
        self.config = config
        self.on_log = on_log
        self.on_progress = on_progress
        self.on_result = on_result
        self.cancellation = cancellation

    def run(self) -> RunStats:
        if self.config.input_dir is None or self.config.output_dir is None:
            raise ValueError("Не выбраны входная и выходная папки")
        if not self.config.input_dir.is_dir():
            raise FileNotFoundError(f"Входная папка не найдена: {self.config.input_dir}")

        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        files = collect_input_files(self.config.input_dir, self.config.recursive)
        stats = RunStats(total=len(files))
        converter = DocumentConverterService(self.config, self._log)

        self._log(LogLevel.INFO, f"Найдено файлов: {len(files)}")
        self._progress(stats, "", "Ожидание")

        for source_path in files:
            if self.cancellation.cancelled:
                self._log(LogLevel.WARNING, "Обработка остановлена пользователем")
                break

            relative_source = source_path.relative_to(self.config.input_dir)
            output_path = unique_output_path(self.config.output_dir, relative_source)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            self._progress(stats, str(relative_source), "Конвертация")
            started = monotonic()
            result: FileResult

            try:
                markdown, metadata = converter.convert(source_path, self.cancellation)
                if self.cancellation.cancelled:
                    self._log(LogLevel.WARNING, f"Файл пропущен из-за остановки: {relative_source}")
                    break

                header = (
                    f"<!-- Источник: {source_path.name} | Метод: {metadata.method} | "
                    f"Конвертирован: {strftime('%Y-%m-%d %H:%M')} | "
                    f"OCR: {'да' if metadata.used_ocr else 'нет'} | "
                    f"Vision: {'да' if metadata.used_vision else 'нет'} -->\n\n"
                )
                temp_path = output_path.with_suffix(output_path.suffix + ".tmp")
                temp_path.write_text(header + markdown, encoding="utf-8")
                temp_path.replace(output_path)

                elapsed = monotonic() - started
                result = FileResult(
                    source_path=source_path,
                    output_path=output_path,
                    ok=True,
                    method=metadata.method,
                    elapsed_seconds=elapsed,
                    used_ocr=metadata.used_ocr,
                    used_vision=metadata.used_vision,
                )
                stats.success += 1
                if metadata.used_ocr:
                    stats.ocr_files += 1
                if metadata.used_vision:
                    stats.vision_files += 1
                self._log(LogLevel.SUCCESS, f"Готово: {relative_source} -> {output_path.name}")
            except Exception as exc:
                elapsed = monotonic() - started
                result = FileResult(
                    source_path=source_path,
                    output_path=None,
                    ok=False,
                    method="error",
                    error=str(exc),
                    elapsed_seconds=elapsed,
                )
                stats.errors += 1
                self._log(LogLevel.ERROR, f"Ошибка: {relative_source}: {exc}")

            stats.processed += 1
            self.on_result(result)
            self._progress(stats, str(relative_source), "Готово" if result.ok else "Ошибка")

        self._progress(stats, "", "Завершено")
        return stats

    def _log(self, level: LogLevel, message: str) -> None:
        self.on_log(LogEvent(level, message))

    def _progress(self, stats: RunStats, current_file: str, stage: str) -> None:
        percent = int(stats.processed / stats.total * 100) if stats.total else 0
        self.on_progress(
            ProgressEvent(
                total_files=stats.total,
                processed_files=stats.processed,
                current_file=current_file,
                current_stage=stage,
                percent=percent,
                eta_seconds=stats.eta_seconds,
            )
        )

