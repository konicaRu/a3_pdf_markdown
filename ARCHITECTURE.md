# A3 PDF Markdown Architecture

## Цель

Desktop-приложение для конвертации документов в Markdown без Jupyter и без ручного запуска скриптов. Пользователь выбирает входную и выходную папки, настраивает обработку, запускает batch job и видит прогресс, логи, ошибки и статистику.

## MVP

Первая версия должна включать:

- выбор input folder;
- выбор output folder;
- настройку основных параметров обработки;
- запуск конвертации;
- stop/cancel обработки;
- общий progress bar;
- текущий файл и текущий этап;
- окно логов в реальном времени;
- панель статистики;
- сохранение настроек между запусками;
- один `.md` файл на каждый исходный файл;
- разрешение конфликтов имен через `name_2.md`, `name_3.md`.

Не входит в MVP:

- полноценный pause/resume;
- ручное управление очередью;
- retry failed из GUI;
- human review mode;
- benchmark UI;
- экспорт дополнительных артефактов рядом с Markdown.

## Технологический стек

- GUI: PySide6.
- Основной конвертер: Microsoft MarkItDown.
- PDF и OCR: PyMuPDF для анализа/рендера страниц, OCR-движок для текста.
- Vision: LM Studio или Ollama для описания графиков, схем, картинок и fallback-страниц.
- Экспериментальный пайплайн: Docling, доступен позже как benchmark/alternative mode.
- Упаковка Windows: PyInstaller или Nuitka после стабилизации MVP.

## Модули

Предлагаемая структура будущего приложения:

```text
a3_pdf_markdown/
  app/
    main.py
    ui/
      main_window.py
      settings_dialog.py
      log_model.py
    core/
      config.py
      models.py
      paths.py
      job_runner.py
      output_naming.py
    converters/
      base.py
      markitdown_converter.py
      pdf_pipeline.py
      vision_client.py
      ocr_engine.py
      docling_experimental.py
    packaging/
      pyinstaller.spec
  scripts/
    microsoft2_markitdown_converter.ipynb
    in в Markdow3_LLM.ipynb
  tests/
  plan.md
  MEMORY.md
  ARCHITECTURE.md
```

## Основной пайплайн

### DOCX/PPTX/XLSX

1. Передать файл в MarkItDown.
2. Если включен vision-провайдер, использовать его для изображений/слайдов там, где MarkItDown поддерживает LLM hooks.
3. Получить Markdown.
4. Сохранить один `.md` файл в output directory с сохранением относительной структуры входной папки.

### PDF

PDF не должен по умолчанию полностью пересказываться vision-моделью.

План обработки:

1. Проанализировать PDF через PyMuPDF.
2. Если есть хороший текстовый слой, извлечь текст без OCR.
3. Если текстовый слой слабый или отсутствует, использовать OCR.
4. Найти страницы/области, где есть графики, схемы, диаграммы, изображения или низкое качество OCR.
5. Для таких страниц/областей вызвать vision-модель.
6. Собрать Markdown из точного текста OCR/текстового слоя и точечных описаний визуальных элементов.
7. Если OCR полностью не справился на странице, использовать vision fallback для этой страницы.

## Vision Strategy

Vision-модель используется для:

- графиков;
- схем;
- диаграмм;
- сложных таблиц в изображениях;
- картинок с важным смыслом;
- страниц, где OCR дал мало текста или мусор.

Vision-модель не используется для:

- полного пересказа каждой страницы в обычном режиме;
- замены нормального OCR;
- создания длинного вольного пересказа вместо извлеченного текста.

## Настройки

Минимальные настройки MVP:

- input directory;
- output directory;
- recursive mode;
- overwrite/conflict mode, по умолчанию `rename`;
- OCR enabled;
- vision enabled;
- vision provider: `LM Studio` или `Ollama`;
- base URL;
- model name;
- workers count;
- PDF render DPI;
- language: `ru`, фиксировано для UI, но может использоваться OCR.

## Потоки и отмена

GUI не выполняет конвертацию в главном UI-потоке.

Модель выполнения:

- `QThread` или `QThreadPool` для background job;
- сигналы Qt для progress/log/statistics;
- cooperative cancellation через общий cancellation token;
- каждый файл завершается атомарно: временный файл пишется первым, затем переименовывается в итоговый `.md`.

## Логи и статистика

Логи:

- INFO;
- SUCCESS;
- WARNING;
- ERROR;
- DEBUG.

Статистика:

- всего файлов;
- обработано;
- успешно;
- ошибки;
- текущий файл;
- среднее время на файл;
- примерный ETA;
- использовался ли OCR;
- использовалась ли vision-модель.

## Git Workflow

Текущая рабочая папка пока не является git-репозиторием.

Нужно выбрать один вариант:

1. Инициализировать git в текущей папке и подключить remote `https://github.com/konicaRu/a3_pdf_markdown.git`.
2. Клонировать репозиторий заново и перенести текущие файлы туда.

Команда пользователя `git save` будет означать:

1. проверить `git status`;
2. добавить релевантные файлы;
3. сделать commit с коротким сообщением;
4. не делать push без отдельной команды пользователя.
