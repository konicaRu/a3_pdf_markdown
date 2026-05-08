from __future__ import annotations

import base64
import io
import json
from dataclasses import dataclass
from typing import Protocol
from urllib import request

from PIL import Image

from a3_pdf_markdown.app.core.models import AppConfig, VisionProvider


class VisionClient(Protocol):
    def describe_image(self, image: Image.Image, prompt: str) -> str:
        ...


@dataclass(slots=True)
class NoopVisionClient:
    def describe_image(self, image: Image.Image, prompt: str) -> str:
        return ""


def image_to_data_url(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def image_to_base64(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")


class OpenAICompatibleVisionClient:
    def __init__(self, base_url: str, model: str, api_key: str = "lm-studio") -> None:
        from openai import OpenAI

        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model = model

    def describe_image(self, image: Image.Image, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_to_data_url(image)}},
                    ],
                }
            ],
            temperature=0.1,
            max_tokens=900,
        )
        return (response.choices[0].message.content or "").strip()


class OllamaVisionClient:
    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def describe_image(self, image: Image.Image, prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                    "images": [image_to_base64(image)],
                }
            ],
            "stream": False,
            "options": {"temperature": 0.1},
        }
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{self.base_url}/api/chat",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
        return (data.get("message", {}).get("content") or "").strip()


def build_vision_client(config: AppConfig) -> VisionClient:
    if not config.vision_enabled:
        return NoopVisionClient()

    if config.vision_provider == VisionProvider.OLLAMA:
        return OllamaVisionClient(config.vision_base_url or "http://localhost:11434", config.vision_model)

    return OpenAICompatibleVisionClient(
        config.vision_base_url or "http://localhost:1234/v1",
        config.vision_model,
    )

