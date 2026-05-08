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


def normalize_output_relative_path(relative_source: Path, lowercase_filename: bool) -> Path:
    if not lowercase_filename:
        return relative_source.with_suffix(".md")
    return relative_source.with_name(relative_source.name.lower()).with_suffix(".md")


def unique_output_path(
    output_dir: Path,
    relative_source: Path,
    lowercase_filename: bool = False,
) -> Path:
    candidate = output_dir / normalize_output_relative_path(relative_source, lowercase_filename)
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
