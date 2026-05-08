from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from a3_pdf_markdown.app.core.models import AppConfig, VisionProvider


CONFIG_PATH = Path.home() / ".a3_pdf_markdown" / "config.json"


def load_config(path: Path = CONFIG_PATH) -> AppConfig:
    if not path.exists():
        return AppConfig()

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return AppConfig()

    config = AppConfig()
    for key, value in raw.items():
        if not hasattr(config, key):
            continue
        if key in {"input_dir", "output_dir"} and value:
            value = Path(value)
        if key == "vision_provider":
            value = VisionProvider(value)
        setattr(config, key, value)
    return config


def save_config(config: AppConfig, path: Path = CONFIG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = asdict(config)
    data["input_dir"] = str(config.input_dir) if config.input_dir else None
    data["output_dir"] = str(config.output_dir) if config.output_dir else None
    data["vision_provider"] = config.vision_provider.value
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

