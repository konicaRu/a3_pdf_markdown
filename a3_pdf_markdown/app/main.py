from __future__ import annotations

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from a3_pdf_markdown.app.resources import APP_ICON_PATH
from a3_pdf_markdown.app.ui.main_window import MainWindow


def set_windows_app_id() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "A3.PDFMarkdown.Desktop"
        )
    except Exception:
        return


def main() -> int:
    set_windows_app_id()

    app = QApplication(sys.argv)
    app.setApplicationName("A3 PDF Markdown")
    app.setOrganizationName("A3")
    if APP_ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(APP_ICON_PATH)))

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
