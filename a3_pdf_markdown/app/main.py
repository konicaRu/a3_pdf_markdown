from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from a3_pdf_markdown.app.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("A3 PDF Markdown")
    app.setOrganizationName("A3")

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

