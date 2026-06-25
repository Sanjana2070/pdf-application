from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel
from PySide6.QtCore import Signal, Qt
from dataclasses import dataclass


@dataclass
class _NavItem:
    label: str
    key: str
    enabled: bool = True


class Sidebar(QWidget):
    panel_selected = Signal(str)

    _NAV_ITEMS = [
        _NavItem("Compress",    "compress",    enabled=True),
        _NavItem("Convert",     "convert",     enabled=True),
        _NavItem("Edit",        "edit",        enabled=True),
        _NavItem("Merge/Split", "merge_split", enabled=True),
        _NavItem("Reader",      "reader",      enabled=True),
        _NavItem("Forms",       "forms",       enabled=True),
        _NavItem("Sign",        "sign",        enabled=True),
    ]

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setFixedWidth(190)
        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        logo = QLabel("PDF Tools")
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #0078d4;"
            "padding: 20px 0 16px 0; background-color: #252526;"
        )

        self._nav = QListWidget()
        self._nav.setFocusPolicy(Qt.NoFocus)

        for item in self._NAV_ITEMS:
            li = QListWidgetItem(item.label)
            li.setData(Qt.UserRole, item.key)
            if not item.enabled:
                li.setFlags(li.flags() & ~Qt.ItemIsEnabled)
            self._nav.addItem(li)

        layout.addWidget(logo)
        layout.addWidget(self._nav)
        layout.addStretch()

        version = QLabel("v0.4.0 — Complete")
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet("color: #505050; font-size: 11px; padding: 8px;")
        layout.addWidget(version)

    def _connect_signals(self) -> None:
        self._nav.currentItemChanged.connect(self._on_item_changed)

    def _on_item_changed(self, current: QListWidgetItem, previous: QListWidgetItem) -> None:
        if current is None:
            return
        if not (current.flags() & Qt.ItemIsEnabled):
            self._nav.setCurrentItem(previous)
            return
        self.panel_selected.emit(current.data(Qt.UserRole))

    def select_default(self) -> None:
        for i in range(self._nav.count()):
            item = self._nav.item(i)
            if item.data(Qt.UserRole) == "convert":
                self._nav.setCurrentItem(item)
                break
