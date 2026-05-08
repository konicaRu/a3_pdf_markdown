---
# Desktop GUI interface

## Основное требование

Система должна иметь полноценный графический интерфейс пользователя (GUI).

---

# GUI objective

Интерфейс должен позволять пользователю:

- выбрать папку входящих файлов;
- выбрать папку выходных файлов;
- настроить параметры обработки;
- запустить конвертацию;
- видеть прогресс обработки;
- видеть ошибки;
- видеть статус обработки документов.

---

# Основной сценарий использования

## User flow

1. Пользователь запускает приложение.
2. Выбирает input directory.
3. Выбирает output directory.
4. Настраивает параметры.
5. Нажимает кнопку:
   - «Выполнить»
6. Видит:
   - прогресс;
   - статус;
   - количество обработанных файлов;
   - оставшееся время;
   - ошибки.

---

# Main window

## Интерфейс должен содержать

- поле выбора input folder;
- поле выбора output folder;
- кнопку Browse;
- кнопку Execute;
- progress bar;
- toolbar;
- log window;
- statistics panel.

---

# Example UI layout

```text id="8ud97v"
----------------------------------------------------

| Input folder:  [ C:/input              ] [Browse]
|
| Output folder: [ C:/output             ] [Browse]
|
| OCR:        [x]
| Vision:     [x]
| Recursive:  [ ]
|
| Workers:    [ 4 ]
|
|                [ Execute ]
|

----------------------------------------------------

| Progress:  ████████████░░░░░░░  64%
|
| Processed files: 128 / 200
| Current file: report_2025.pdf
| ETA: 00:04:21

----------------------------------------------------

| Logs:
| [OK] report_001.pdf
| [OK] invoice_12.docx
| [ERROR] corrupted_scan.pdf

----------------------------------------------------

```md
---

# Desktop GUI interface

## Основное требование

Система должна иметь полноценный графический интерфейс пользователя (GUI).

---

# GUI objective

Интерфейс должен позволять пользователю:

- выбрать папку входящих файлов;
- выбрать папку выходных файлов;
- настроить параметры обработки;
- запустить конвертацию;
- видеть прогресс обработки;
- видеть ошибки;
- видеть статус обработки документов.

---

# Основной сценарий использования

## User flow

1. Пользователь запускает приложение.
2. Выбирает input directory.
3. Выбирает output directory.
4. Настраивает параметры.
5. Нажимает кнопку:
   - «Выполнить»
6. Видит:
   - прогресс;
   - статус;
   - количество обработанных файлов;
   - оставшееся время;
   - ошибки.

---

# Main window

## Интерфейс должен содержать

- поле выбора input folder;
- поле выбора output folder;
- кнопку Browse;
- кнопку Execute;
- progress bar;
- toolbar;
- log window;
- statistics panel.

---

# Example UI layout

```text id="8ud97v"
----------------------------------------------------
| Input folder:  [ C:/input              ] [Browse]
|
| Output folder: [ C:/output             ] [Browse]
|
| OCR:        [x]
| Vision:     [x]
| Recursive:  [ ]
|
| Workers:    [ 4 ]
|
|                [ Execute ]
|
----------------------------------------------------
| Progress:  ████████████░░░░░░░  64%
|
| Processed files: 128 / 200
| Current file: report_2025.pdf
| ETA: 00:04:21
----------------------------------------------------
| Logs:
| [OK] report_001.pdf
| [OK] invoice_12.docx
| [ERROR] corrupted_scan.pdf
----------------------------------------------------
```

---

# Folder picker

## Требование

Пользователь должен иметь возможность выбирать папки через:

- native file dialog;

- drag-and-drop.

---

# Drag and drop support

## Возможность

Поддерживать:

- drag-and-drop folders;

- drag-and-drop files.

---

# Execute button

## Требование

Кнопка:

- запускает batch processing;

- блокируется во время обработки;

- активируется после завершения.

---

# Stop button

## Дополнительная возможность

Добавить кнопку:

- Stop;

- Cancel processing.

---

# Progress bar

## Требование

Progress bar должен отображать:

- общий прогресс;

- текущий файл;

- текущую страницу;

- OCR progress;

- batch progress.

---

# Toolbar

## Toolbar должен содержать

- Start;

- Stop;

- Open output folder;

- Settings;

- Clear logs;

- Export logs.

---

# Statistics panel

## Показывать

- количество файлов;

- количество успешных файлов;

- количество ошибок;

- среднее время обработки;

- OCR usage;

- Vision usage.

---

# Real-time logs

## Требование

Показывать логи в реальном времени.

---

# Log severity

## Поддержка

- INFO

- WARNING

- ERROR

- DEBUG

---

# Log coloring

## Желательно

- INFO → серый

- SUCCESS → зеленый

- WARNING → желтый

- ERROR → красный

---

# Current document preview

## Дополнительная возможность

Показывать:

- текущую страницу;

- preview Markdown;

- extracted image;

- OCR blocks.

---

# Queue management

## Требование

GUI должен поддерживать очередь документов.

---

# Queue features

- pause;

- resume;

- retry failed;

- remove from queue.

---

# Multi-file support

## Требование

Обрабатывать:

- сотни файлов;

- тысячи файлов;

- большие batch jobs.

---

# GUI framework

## Предпочтительные варианты

### Option 1

PySide6 / Qt

### Option 2

PyQt6

### Option 3

Electron + Python backend

---

# Recommended choice

## Предпочтительно использовать

PySide6.

---

# Почему PySide6

- современный UI;

- стабильность;

- threading support;

- progress bars;

- native dialogs;

- хорошая работа с multiprocessing;

- cross-platform.

---

# Threading model

## Важно

GUI не должен зависать во время обработки.

---

# Требование

OCR и parsing должны выполняться:

- в worker threads;

- в background processes.

---

# UI responsiveness

## Требование

Во время обработки:

- интерфейс остается responsive;

- progress обновляется в реальном времени;

- logs обновляются в реальном времени.

---

# Error window

## Возможность

Отдельное окно:

- stacktrace;

- error details;

- failed document.

---

# Retry failed documents

## Требование

Пользователь должен иметь возможность:

- повторно обработать только failed files.

---

# Open output folder

## Toolbar action

Кнопка должна:

- открывать output folder в explorer/finder.

---

# Settings window

## Настройки

- OCR engine;

- Vision provider;

- workers count;

- GPU usage;

- overwrite mode;

- chunking mode;

- language settings.

---

# Settings persistence

## Требование

Настройки должны сохраняться между запусками.

---

# Example config

```json
{
  "input_dir": "C:/input",
  "output_dir": "C:/output",
  "ocr": true,
  "vision": true,
  "workers": 4
}
```

---

# Dark mode

## Желательно

Поддержка:

- dark mode;

- light mode.

---

# Internationalization

## Возможность

Поддержка:

- русского;

- английского интерфейса.

---

# File processing visualization

## Возможность

Показывать pipeline stages:

- Parsing

- OCR

- Vision

- Markdown generation

- Cleanup

- Save

---

# Example stage visualization

```text
report.pdf

[✓] Parsing
[✓] OCR
[✓] Vision
[ ] Markdown cleanup
[ ] Save
```

---

# ETA estimation

## Требование

Показывать:

- estimated remaining time;

- average speed.

---

# Notifications

## Возможность

Показывать:

- processing completed;

- errors;

- batch finished.

---

# Auto-open result

## Возможность

После завершения:

- автоматически открыть output folder.

---

# Benchmark GUI mode

## Дополнительная возможность

GUI для:

- сравнения pipelines;

- benchmark testing;

- visual comparison Markdown.

---

# Human review mode

## Возможность

Показывать:

- original document;

- generated Markdown;

- OCR blocks;

- extracted tables.

---

# Final GUI objective

Интерфейс должен позволять пользователю без технических знаний:

- выбрать папки;

- нажать кнопку «Выполнить»;

- наблюдать прогресс;

- получать качественный Markdown;

- видеть ошибки и статус обработки в реальном времени.
