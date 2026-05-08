from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from a3_pdf_markdown.app.core.config import load_config, save_config
from a3_pdf_markdown.app.core.job_runner import CancellationToken, JobRunner
from a3_pdf_markdown.app.core.models import (
    AppConfig,
    FileResult,
    LogEvent,
    LogLevel,
    ProgressEvent,
    RunStats,
    VisionProvider,
)


def format_eta(seconds: float | None) -> str:
    if seconds is None:
        return "--:--"
    total = max(0, int(seconds))
    minutes, sec = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{sec:02d}"


class Worker(QObject):
    log = Signal(object)
    progress = Signal(object)
    result = Signal(object)
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, config: AppConfig, cancellation: CancellationToken) -> None:
        super().__init__()
        self.config = config
        self.cancellation = cancellation

    @Slot()
    def run(self) -> None:
        try:
            runner = JobRunner(
                self.config,
                on_log=self.log.emit,
                on_progress=self.progress.emit,
                on_result=self.result.emit,
                cancellation=self.cancellation,
            )
            stats = runner.run()
            self.finished.emit(stats)
        except Exception as exc:
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("A3 PDF Markdown")
        self.resize(1060, 720)

        self.config = load_config()
        self.thread: QThread | None = None
        self.worker: Worker | None = None
        self.cancellation: CancellationToken | None = None

        self._build_ui()
        self._load_config_to_ui()

    def _build_ui(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)

        paths_group = QGroupBox("Папки")
        paths_layout = QGridLayout(paths_group)

        self.input_edit = QLineEdit()
        self.output_edit = QLineEdit()
        input_button = QPushButton("Обзор")
        output_button = QPushButton("Обзор")
        input_button.clicked.connect(self._choose_input_dir)
        output_button.clicked.connect(self._choose_output_dir)

        paths_layout.addWidget(QLabel("Входная папка"), 0, 0)
        paths_layout.addWidget(self.input_edit, 0, 1)
        paths_layout.addWidget(input_button, 0, 2)
        paths_layout.addWidget(QLabel("Выходная папка"), 1, 0)
        paths_layout.addWidget(self.output_edit, 1, 1)
        paths_layout.addWidget(output_button, 1, 2)
        layout.addWidget(paths_group)

        settings_group = QGroupBox("Настройки")
        settings_layout = QFormLayout(settings_group)

        self.recursive_check = QCheckBox("Обрабатывать вложенные папки")
        self.lowercase_check = QCheckBox("Имя .md в нижний регистр")
        self.ocr_check = QCheckBox("OCR")
        self.vision_check = QCheckBox("Vision")

        self.provider_combo = QComboBox()
        self.provider_combo.addItem("LM Studio", VisionProvider.LM_STUDIO.value)
        self.provider_combo.addItem("Ollama", VisionProvider.OLLAMA.value)
        self.provider_combo.currentIndexChanged.connect(self._provider_changed)

        self.base_url_edit = QLineEdit()
        self.model_edit = QLineEdit()

        self.workers_spin = QSpinBox()
        self.workers_spin.setRange(1, 16)
        self.workers_spin.setValue(1)

        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(72, 300)
        self.dpi_spin.setSingleStep(25)

        toggles = QHBoxLayout()
        toggles.addWidget(self.recursive_check)
        toggles.addWidget(self.lowercase_check)
        toggles.addWidget(self.ocr_check)
        toggles.addWidget(self.vision_check)
        toggles.addStretch(1)

        settings_layout.addRow("Режим", toggles)
        settings_layout.addRow("Провайдер vision", self.provider_combo)
        settings_layout.addRow("Base URL", self.base_url_edit)
        settings_layout.addRow("Модель", self.model_edit)
        settings_layout.addRow("Workers", self.workers_spin)
        settings_layout.addRow("PDF DPI", self.dpi_spin)
        layout.addWidget(settings_group)

        actions = QHBoxLayout()
        self.start_button = QPushButton("Выполнить")
        self.stop_button = QPushButton("Остановить")
        self.stop_button.setEnabled(False)
        self.start_button.clicked.connect(self._start)
        self.stop_button.clicked.connect(self._stop)
        actions.addWidget(self.start_button)
        actions.addWidget(self.stop_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        progress_group = QGroupBox("Прогресс")
        progress_layout = QGridLayout(progress_group)
        self.progress_bar = QProgressBar()
        self.current_file_label = QLabel("-")
        self.current_stage_label = QLabel("-")
        self.stats_label = QLabel("Файлов: 0 | Успешно: 0 | Ошибки: 0 | ETA: --:--")
        progress_layout.addWidget(self.progress_bar, 0, 0, 1, 2)
        progress_layout.addWidget(QLabel("Текущий файл"), 1, 0)
        progress_layout.addWidget(self.current_file_label, 1, 1)
        progress_layout.addWidget(QLabel("Этап"), 2, 0)
        progress_layout.addWidget(self.current_stage_label, 2, 1)
        progress_layout.addWidget(self.stats_label, 3, 0, 1, 2)
        layout.addWidget(progress_group)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumHeight(220)
        layout.addWidget(self.log_view, stretch=1)

        self.setCentralWidget(central)

    def _load_config_to_ui(self) -> None:
        self.input_edit.setText(str(self.config.input_dir) if self.config.input_dir else "")
        self.output_edit.setText(str(self.config.output_dir) if self.config.output_dir else "")
        self.recursive_check.setChecked(self.config.recursive)
        self.lowercase_check.setChecked(self.config.lowercase_output_filename)
        self.ocr_check.setChecked(self.config.ocr_enabled)
        self.vision_check.setChecked(self.config.vision_enabled)
        index = self.provider_combo.findData(self.config.vision_provider.value)
        self.provider_combo.setCurrentIndex(max(0, index))
        self.base_url_edit.setText(self.config.vision_base_url)
        self.model_edit.setText(self.config.vision_model)
        self.workers_spin.setValue(self.config.workers)
        self.dpi_spin.setValue(self.config.pdf_render_dpi)

    def _collect_config(self) -> AppConfig:
        provider = VisionProvider(self.provider_combo.currentData())
        return AppConfig(
            input_dir=Path(self.input_edit.text()) if self.input_edit.text().strip() else None,
            output_dir=Path(self.output_edit.text()) if self.output_edit.text().strip() else None,
            recursive=self.recursive_check.isChecked(),
            lowercase_output_filename=self.lowercase_check.isChecked(),
            ocr_enabled=self.ocr_check.isChecked(),
            vision_enabled=self.vision_check.isChecked(),
            vision_provider=provider,
            vision_base_url=self.base_url_edit.text().strip(),
            vision_model=self.model_edit.text().strip(),
            workers=self.workers_spin.value(),
            pdf_render_dpi=self.dpi_spin.value(),
        )

    def _choose_input_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Выберите входную папку")
        if directory:
            self.input_edit.setText(directory)

    def _choose_output_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Выберите выходную папку")
        if directory:
            self.output_edit.setText(directory)

    def _provider_changed(self) -> None:
        provider = VisionProvider(self.provider_combo.currentData())
        if provider == VisionProvider.OLLAMA:
            if not self.base_url_edit.text() or "1234" in self.base_url_edit.text():
                self.base_url_edit.setText("http://localhost:11434")
            if not self.model_edit.text() or "qwen/qwen" in self.model_edit.text():
                self.model_edit.setText("qwen2.5vl:7b")
        else:
            if not self.base_url_edit.text() or "11434" in self.base_url_edit.text():
                self.base_url_edit.setText("http://localhost:1234/v1")
            if not self.model_edit.text() or self.model_edit.text() == "qwen2.5vl:7b":
                self.model_edit.setText("qwen/qwen2.5-vl-7b")

    def _start(self) -> None:
        config = self._collect_config()
        if config.input_dir is None or config.output_dir is None:
            QMessageBox.warning(self, "Не хватает данных", "Выберите входную и выходную папки.")
            return

        self.config = config
        save_config(config)
        self.log_view.clear()
        self.progress_bar.setValue(0)
        self._set_running(True)

        self.cancellation = CancellationToken()
        self.thread = QThread(self)
        self.worker = Worker(config, self.cancellation)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.log.connect(self._append_log)
        self.worker.progress.connect(self._update_progress)
        self.worker.result.connect(self._handle_result)
        self.worker.finished.connect(self._finished)
        self.worker.failed.connect(self._failed)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self._clear_thread_refs)
        self.thread.start()

    def _stop(self) -> None:
        if self.cancellation is not None:
            self.cancellation.cancel()
            self.stop_button.setEnabled(False)
            self._append_log(LogEvent(LogLevel.WARNING, "Остановка запрошена. Текущий файл завершится безопасно."))

    @Slot(object)
    def _append_log(self, event: LogEvent) -> None:
        color = {
            LogLevel.DEBUG: QColor("#6b7280"),
            LogLevel.INFO: QColor("#374151"),
            LogLevel.SUCCESS: QColor("#047857"),
            LogLevel.WARNING: QColor("#b45309"),
            LogLevel.ERROR: QColor("#b91c1c"),
        }.get(event.level, QColor("#111827"))
        fmt = QTextCharFormat()
        fmt.setForeground(color)
        cursor = self.log_view.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(f"[{event.level.value}] {event.message}\n", fmt)
        self.log_view.setTextCursor(cursor)
        self.log_view.ensureCursorVisible()

    @Slot(object)
    def _update_progress(self, event: ProgressEvent) -> None:
        self.progress_bar.setValue(event.percent)
        self.current_file_label.setText(event.current_file or "-")
        self.current_stage_label.setText(event.current_stage or "-")
        self.stats_label.setText(
            f"Файлов: {event.processed_files}/{event.total_files} | ETA: {format_eta(event.eta_seconds)}"
        )

    @Slot(object)
    def _handle_result(self, result: FileResult) -> None:
        if result.ok:
            return
        self._append_log(LogEvent(LogLevel.ERROR, result.error or "Неизвестная ошибка"))

    @Slot(object)
    def _finished(self, stats: RunStats) -> None:
        self._set_running(False)
        self.stats_label.setText(
            f"Файлов: {stats.processed}/{stats.total} | "
            f"Успешно: {stats.success} | Ошибки: {stats.errors} | "
            f"OCR: {stats.ocr_files} | Vision: {stats.vision_files}"
        )
        self._append_log(LogEvent(LogLevel.SUCCESS, "Обработка завершена"))

    @Slot(str)
    def _failed(self, message: str) -> None:
        self._set_running(False)
        self._append_log(LogEvent(LogLevel.ERROR, message))
        QMessageBox.critical(self, "Ошибка", message)

    def _set_running(self, running: bool) -> None:
        self.start_button.setEnabled(not running)
        self.stop_button.setEnabled(running)
        self.input_edit.setEnabled(not running)
        self.output_edit.setEnabled(not running)

    @Slot()
    def _clear_thread_refs(self) -> None:
        self.thread = None
        self.worker = None
        self.cancellation = None

    def closeEvent(self, event) -> None:
        if self.thread is not None and self.thread.isRunning():
            if self.cancellation is not None:
                self.cancellation.cancel()
            self.thread.quit()
            self.thread.wait(3000)
        super().closeEvent(event)
