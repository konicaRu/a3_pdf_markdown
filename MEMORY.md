# Project Memory

## 2026-05-08

Контекст проекта: создается desktop-приложение для batch-конвертации документов в Markdown.

Основные решения:

- Первая стабильная версия строится вокруг Microsoft MarkItDown.
- Docling остается экспериментальным/benchmark-пайплайном, не основным маршрутом MVP.
- GUI: PySide6, только русский интерфейс.
- MVP GUI включает выбор input/output папок, настройки, запуск, stop/cancel, progress, logs, статистику.
- Расширенные функции вроде pause/resume/retry/remove из очереди откладываются после MVP.
- На выходе нужен только один `.md` файл на каждый исходный документ.
- При конфликте имени выходного файла создавать `name_2.md`, `name_3.md` и так далее.
- Основные типы нагрузки: десятки и сотни файлов, преимущественно PDF-сканы и PPTX.
- LLM-провайдеры первой версии: LM Studio и Ollama.
- Желательна упаковка в Windows `.exe`, если это не сильно усложнит проект.
- Git-процесс: пользователь хочет сохранять изменения по команде `git save`.

Решение по PDF:

- Не делать полный пересказ каждой страницы через vision-модель как основной путь, потому что это медленно и может давать пересказ вместо точного Markdown.
- Базовый путь: извлекать текст через OCR/текстовый слой.
- Vision-модель использовать точечно для графиков, схем, картинок и сложных визуальных блоков.
- Если OCR не справляется или дает слишком слабый результат, использовать vision-модель как fallback для проблемной страницы/фрагмента.

Текущие исходники:

- `scripts/microsoft2_markitdown_converter.ipynb` - основной прототип MarkItDown + EasyOCR + PyMuPDF + LM Studio/Qwen VL.
- `scripts/in в Markdow3_LLM.ipynb` - экспериментальный прототип Docling + RapidOCR + LM Studio.
- `plan.md` - исходный план GUI, в нем есть продублированный блок markdown, который позже стоит почистить.

Открытые вопросы:

- Git настроен в текущей папке, remote: `https://github.com/konicaRu/a3_pdf_markdown.git`.
- Команда `git save` настроена как локальный git alias: делает `git add -A` и `git commit -m`.
- Push в GitHub делается отдельной командой `git push`.

## 2026-05-08 MVP scaffold

Создан первый каркас приложения:

- `pyproject.toml` с зависимостями PySide6, MarkItDown, PyMuPDF, EasyOCR, OpenAI client.
- `a3_pdf_markdown/app/main.py` - точка входа.
- `a3_pdf_markdown/app/ui/main_window.py` - MVP GUI.
- `a3_pdf_markdown/app/core/` - конфиг, модели, сбор файлов, runner.
- `a3_pdf_markdown/app/converters/` - MarkItDown service, PDF pipeline, OCR, vision clients.

Проверки:

- `uv run python -m compileall a3_pdf_markdown` - успешно.
- Импорт `AppConfig` и `DocumentConverterService` - успешно.

Техническая заметка:

- Проект ограничен `requires-python = ">=3.11,<3.14"`, потому что OCR-зависимости, в частности `onnxruntime`, пока не поддерживают CPython 3.14.
