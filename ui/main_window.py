from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QStackedWidget

from ui.sidebar import Sidebar
from ui.panels.compress_panel import CompressPanel
from ui.panels.convert_panel import ConvertPanel
from ui.panels.edit_panel import EditPanel
from ui.panels.forms_panel import FormsPanel
from ui.panels.merge_split_panel import MergeSplitPanel
from ui.panels.reader_panel import ReaderPanel
from ui.panels.sign_panel import SignPanel


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self._build_ui()
        self._connect_signals()
        self._sidebar.select_default()

    def _build_ui(self) -> None:
        self.setWindowTitle("PDF Tools")
        self.setMinimumSize(1000, 650)
        self.resize(1200, 750)

        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._sidebar = Sidebar()

        self._stack = QStackedWidget()
        self._stack.setObjectName("panelStack")

        self._panels: dict[str, QWidget] = {
            "compress":    CompressPanel(),
            "convert":     ConvertPanel(),
            "edit":        EditPanel(),
            "merge_split": MergeSplitPanel(),
            "reader":      ReaderPanel(),
            "forms":       FormsPanel(),
            "sign":        SignPanel(),
        }
        for panel in self._panels.values():
            self._stack.addWidget(panel)

        root.addWidget(self._sidebar)
        root.addWidget(self._stack, stretch=1)

    def _connect_signals(self) -> None:
        self._sidebar.panel_selected.connect(self._switch_panel)

    def _switch_panel(self, key: str) -> None:
        panel = self._panels.get(key)
        if panel is not None:
            self._stack.setCurrentWidget(panel)
