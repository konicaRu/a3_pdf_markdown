# A3 PDF Markdown

Desktop-приложение для конвертации PDF, DOCX, PPTX и XLSX в Markdown.

Текущий статус: собран первый MVP-каркас на PySide6 с основным пайплайном MarkItDown и отдельной обработкой PDF через текстовый слой/OCR/vision fallback.

## Возможности MVP

- выбор входной и выходной папки;
- рекурсивный или обычный обход файлов;
- опциональное приведение имени выходного `.md` файла к нижнему регистру;
- конвертация в один `.md` файл на каждый исходный документ;
- безопасное создание `name_2.md`, `name_3.md` при конфликте имен;
- stop/cancel для batch job;
- прогресс, текущий файл, этап обработки;
- логи INFO/SUCCESS/WARNING/ERROR;
- статистика по успешным файлам, ошибкам, OCR и Vision;
- сохранение настроек между запусками.

## Запуск

Двойным кликом по файлу:

```text
A3 PDF Markdown.vbs
```

Если нужно увидеть ошибку запуска в консоли:

```text
A3 PDF Markdown.cmd
```

Из PowerShell:

```powershell
uv run a3-pdf-markdown
```

Альтернативно:

```powershell
uv run python -m a3_pdf_markdown.app.main
```

## Vision providers

Поддерживаются два режима:

- LM Studio: OpenAI-compatible endpoint, по умолчанию `http://localhost:1234/v1`;
- Ollama: endpoint `http://localhost:11434`.

PDF не пересказывается vision-моделью целиком. Основной текст берется из текстового слоя или OCR, а vision используется точечно для графиков, схем, картинок и страниц, где OCR дал слабый результат.

## Разработка

Проверка синтаксиса:

```powershell
uv run python -m compileall a3_pdf_markdown
```

Сохранить изменения локальным commit:

```powershell
git save "сообщение"
```

Отправить в GitHub:

```powershell
git push
```
