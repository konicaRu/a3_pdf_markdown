from __future__ import annotations

from pathlib import Path


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".pptx",
    ".xlsx",
}


def collect_input_files(input_dir: Path, recursive: bool) -> list[Path]:
    iterator = input_dir.rglob("*") if recursive else input_dir.iterdir()
    files = [
        path
        for path in iterator
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    return sorted(files, key=lambda item: str(item).lower())


def unique_output_path(output_dir: Path, relative_source: Path) -> Path:
    candidate = output_dir / relative_source.with_suffix(".md")
    if not candidate.exists():
        return candidate

    parent = candidate.parent
    stem = candidate.stem
    suffix = candidate.suffix
    counter = 2
    while True:
        next_candidate = parent / f"{stem}_{counter}{suffix}"
        if not next_candidate.exists():
            return next_candidate
        counter += 1

