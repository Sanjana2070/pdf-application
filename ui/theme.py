from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor

DARK_BG = "#1e1e1e"
SIDEBAR_BG = "#252526"
ACCENT = "#0078d4"
TEXT_PRIMARY = "#ffffff"
TEXT_MUTED = "#888888"
PANEL_BG = "#2d2d2d"
BORDER_COLOR = "#3a3a3a"

_QSS = """
QMainWindow, QDialog {
    background-color: #1e1e1e;
}

QWidget {
    background-color: #1e1e1e;
    color: #ffffff;
    font-family: 'Segoe UI';
    font-size: 13px;
}

QStackedWidget > QWidget {
    background-color: #2d2d2d;
}

/* Sidebar */
QListWidget {
    background-color: #252526;
    border: none;
    outline: none;
}
QListWidget::item {
    padding: 12px 16px;
    border-radius: 4px;
}
QListWidget::item:selected {
    background-color: #0078d4;
    color: #ffffff;
}
QListWidget::item:hover:!selected:enabled {
    background-color: #37373d;
}
QListWidget::item:disabled {
    color: #505050;
    background-color: transparent;
}

/* Primary action button */
QPushButton#primaryButton {
    background-color: #0078d4;
    color: #ffffff;
    border: none;
    border-radius: 4px;
    padding: 10px 24px;
    font-weight: bold;
    font-size: 13px;
}
QPushButton#primaryButton:hover {
    background-color: #106ebe;
}
QPushButton#primaryButton:pressed {
    background-color: #005a9e;
}
QPushButton#primaryButton:disabled {
    background-color: #3a3a3a;
    color: #666666;
}

/* Regular buttons */
QPushButton {
    background-color: #3a3a3a;
    color: #ffffff;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 6px 16px;
}
QPushButton:hover {
    background-color: #4a4a4a;
    border-color: #666666;
}
QPushButton:pressed {
    background-color: #2a2a2a;
}
QPushButton:disabled {
    color: #666666;
    border-color: #444444;
}

/* Progress bar */
QProgressBar {
    background-color: #3a3a3a;
    border: none;
    border-radius: 3px;
    max-height: 6px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #0078d4;
    border-radius: 3px;
}

/* Panel title */
QLabel#panelTitle {
    font-size: 20px;
    font-weight: bold;
    color: #ffffff;
    padding-bottom: 8px;
}

/* Drop zone hint */
QLabel#dropHint {
    color: #888888;
    font-size: 14px;
    border: 2px dashed #444444;
    border-radius: 8px;
    padding: 40px;
    min-height: 120px;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid #3a3a3a;
    border-radius: 4px;
    background-color: #2d2d2d;
}
QTabBar::tab {
    background-color: #252526;
    color: #aaaaaa;
    padding: 8px 24px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #2d2d2d;
    color: #ffffff;
}
QTabBar::tab:hover:!selected {
    background-color: #37373d;
    color: #cccccc;
}

/* Scroll bars */
QScrollBar:vertical {
    background-color: #2d2d2d;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background-color: #555555;
    border-radius: 5px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background-color: #777777;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* SpinBox */
QSpinBox {
    background-color: #3a3a3a;
    color: #ffffff;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 4px 8px;
}
QSpinBox::up-button, QSpinBox::down-button {
    background-color: #4a4a4a;
    border: none;
    width: 16px;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: #5a5a5a;
}
"""


def apply_theme(app: QApplication) -> None:
    app.setStyleSheet(_QSS)

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(DARK_BG))
    palette.setColor(QPalette.WindowText, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.Base, QColor(PANEL_BG))
    palette.setColor(QPalette.AlternateBase, QColor(SIDEBAR_BG))
    palette.setColor(QPalette.Text, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.Button, QColor(BORDER_COLOR))
    palette.setColor(QPalette.ButtonText, QColor(TEXT_PRIMARY))
    palette.setColor(QPalette.Highlight, QColor(ACCENT))
    palette.setColor(QPalette.HighlightedText, QColor(TEXT_PRIMARY))
    app.setPalette(palette)
