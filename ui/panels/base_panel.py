from PySide6.QtWidgets import QWidget, QProgressBar, QLabel
from PySide6.QtCore import Qt


class BasePanel(QWidget):
    _accepted_extensions: set[str] = set()

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setAcceptDrops(True)

        self._status_label = QLabel("")
        self._status_label.setWordWrap(True)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.hide()

    # ── Drag-and-drop ────────────────────────────────────────────────────────

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            paths = [u.toLocalFile() for u in event.mimeData().urls()]
            if self._all_accepted(paths):
                event.acceptProposedAction()
                self._on_drag_enter_visual()
                return
        event.ignore()

    def dragMoveEvent(self, event) -> None:
        event.acceptProposedAction()

    def dragLeaveEvent(self, event) -> None:
        self._on_drag_leave_visual()

    def dropEvent(self, event) -> None:
        paths = [u.toLocalFile() for u in event.mimeData().urls()]
        self._on_drag_leave_visual()
        event.acceptProposedAction()
        self.handle_dropped_files(paths)

    def _all_accepted(self, paths: list[str]) -> bool:
        if not self._accepted_extensions:
            return True
        return all(
            any(p.lower().endswith(ext) for ext in self._accepted_extensions)
            for p in paths
        )

    def _on_drag_enter_visual(self) -> None:
        pass

    def _on_drag_leave_visual(self) -> None:
        pass

    # ── Subclass contract ────────────────────────────────────────────────────

    def handle_dropped_files(self, paths: list[str]) -> None:
        raise NotImplementedError

    # ── Status / progress ────────────────────────────────────────────────────

    def show_progress(self, visible: bool = True) -> None:
        if visible:
            self._progress_bar.setValue(0)
            self._progress_bar.show()
        else:
            self._progress_bar.hide()

    def set_progress(self, value: int) -> None:
        self._progress_bar.setValue(value)

    def show_status(self, message: str, is_error: bool = False) -> None:
        color = "#e05252" if is_error else "#52c07a"
        self._status_label.setStyleSheet(f"color: {color}; padding: 4px 0;")
        self._status_label.setText(message)
