from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from time import monotonic


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"


class VisionProvider(str, Enum):
    LM_STUDIO = "lm_studio"
    OLLAMA = "ollama"


@dataclass(slots=True)
class AppConfig:
    input_dir: Path | None = None
    output_dir: Path | None = None
    recursive: bool = False
    ocr_enabled: bool = True
    vision_enabled: bool = True
    vision_provider: VisionProvider = VisionProvider.LM_STUDIO
    vision_base_url: str = "http://localhost:1234/v1"
    vision_model: str = "qwen/qwen2.5-vl-7b"
    workers: int = 1
    pdf_render_dpi: int = 150
    min_text_chars_per_page: int = 80


@dataclass(slots=True)
class LogEvent:
    level: LogLevel
    message: str


@dataclass(slots=True)
class ProgressEvent:
    total_files: int
    processed_files: int
    current_file: str = ""
    current_stage: str = ""
    percent: int = 0
    eta_seconds: float | None = None


@dataclass(slots=True)
class FileResult:
    source_path: Path
    output_path: Path | None
    ok: bool
    method: str
    error: str | None = None
    elapsed_seconds: float = 0.0
    used_ocr: bool = False
    used_vision: bool = False


@dataclass(slots=True)
class RunStats:
    total: int = 0
    processed: int = 0
    success: int = 0
    errors: int = 0
    ocr_files: int = 0
    vision_files: int = 0
    started_at: float = field(default_factory=monotonic)

    @property
    def average_seconds(self) -> float:
        if self.processed == 0:
            return 0.0
        return (monotonic() - self.started_at) / self.processed

    @property
    def eta_seconds(self) -> float | None:
        remaining = self.total - self.processed
        if self.processed == 0 or remaining <= 0:
            return None
        return remaining * self.average_seconds

