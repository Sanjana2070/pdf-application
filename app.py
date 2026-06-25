import os
import sys

os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from ui.main_window import MainWindow
from ui.theme import apply_theme


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("PDF Tools")
    app.setOrganizationName("PDFTools")
    app.setApplicationVersion("0.1.0")

    apply_theme(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
