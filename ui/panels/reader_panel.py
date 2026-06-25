import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QSizePolicy, QFileDialog, QSpinBox, QFrame
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QImage, QKeySequence, QShortcut, QWheelEvent

from workers.worker import Worker
from services.convert_service import render_page


_ZOOM_STEPS = [0.25, 0.33, 0.50, 0.67, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0]


class _PageView(QLabel):
    """QLabel that centres the page pixmap and accepts drops."""
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("background-color: #404040;")


class ReaderPanel(QWidget):
    """
    PDF reader panel — not derived from BasePanel because its layout
    (toolbar + scroll area) is structurally different from tool panels.
    Drag-and-drop is handled directly.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

        self._pdf_path: str = ""
        self._page_count: int = 0
        self._current_page: int = 0
        self._zoom: float = 1.0
        self._page_width_pts: float = 595.0  # updated after first render
        self._page_height_pts: float = 842.0
        self._worker: Worker | None = None
        self._pending_render: bool = False  # flag to coalesce rapid requests

        self._build_ui()
        self._connect_signals()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_toolbar())
        layout.addWidget(self._build_scroll_area(), stretch=1)
        layout.addWidget(self._build_status_bar())

    def _build_toolbar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(44)
        bar.setStyleSheet("background-color: #2d2d2d; border-bottom: 1px solid #3a3a3a;")

        h = QHBoxLayout(bar)
        h.setContentsMargins(8, 4, 8, 4)
        h.setSpacing(6)

        # Open
        self._btn_open = QPushButton("Open PDF")
        self._btn_open.setFixedWidth(90)

        sep1 = self._make_sep()

        # Navigation
        self._btn_prev = QPushButton("◀")
        self._btn_prev.setFixedWidth(30)
        self._btn_prev.setEnabled(False)

        self._page_spin = QSpinBox()
        self._page_spin.setRange(1, 1)
        self._page_spin.setFixedWidth(55)
        self._page_spin.setEnabled(False)

        self._page_total = QLabel("/ —")
        self._page_total.setStyleSheet("color: #aaaaaa;")
        self._page_total.setFixedWidth(40)

        self._btn_next = QPushButton("▶")
        self._btn_next.setFixedWidth(30)
        self._btn_next.setEnabled(False)

        sep2 = self._make_sep()

        # Zoom
        self._btn_zoom_out = QPushButton("−")
        self._btn_zoom_out.setFixedWidth(30)
        self._btn_zoom_out.setEnabled(False)

        self._zoom_label = QLabel("100%")
        self._zoom_label.setAlignment(Qt.AlignCenter)
        self._zoom_label.setFixedWidth(52)
        self._zoom_label.setStyleSheet("color: #cccccc;")

        self._btn_zoom_in = QPushButton("+")
        self._btn_zoom_in.setFixedWidth(30)
        self._btn_zoom_in.setEnabled(False)

        self._btn_fit_width = QPushButton("Fit Width")
        self._btn_fit_width.setFixedWidth(78)
        self._btn_fit_width.setEnabled(False)

        self._btn_fit_page = QPushButton("Fit Page")
        self._btn_fit_page.setFixedWidth(72)
        self._btn_fit_page.setEnabled(False)

        h.addWidget(self._btn_open)
        h.addWidget(sep1)
        h.addWidget(self._btn_prev)
        h.addWidget(self._page_spin)
        h.addWidget(self._page_total)
        h.addWidget(self._btn_next)
        h.addWidget(sep2)
        h.addWidget(self._btn_zoom_out)
        h.addWidget(self._zoom_label)
        h.addWidget(self._btn_zoom_in)
        h.addWidget(self._btn_fit_width)
        h.addWidget(self._btn_fit_page)
        h.addStretch()
        return bar

    def _build_scroll_area(self) -> QScrollArea:
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(False)
        self._scroll.setAlignment(Qt.AlignCenter)
        self._scroll.setStyleSheet("QScrollArea { border: none; background-color: #404040; }")

        self._page_view = _PageView()
        self._page_view.setText("Open a PDF to start reading")
        self._page_view.setStyleSheet(
            "background-color: #404040; color: #888888; font-size: 16px;"
        )

        self._scroll.setWidget(self._page_view)
        return self._scroll

    def _build_status_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(24)
        bar.setStyleSheet("background-color: #252526; border-top: 1px solid #3a3a3a;")
        h = QHBoxLayout(bar)
        h.setContentsMargins(8, 0, 8, 0)
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #888888; font-size: 11px;")
        h.addWidget(self._status_label)
        h.addStretch()
        return bar

    @staticmethod
    def _make_sep() -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("color: #3a3a3a;")
        sep.setFixedWidth(1)
        return sep

    # ── Signals & shortcuts ───────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        self._btn_open.clicked.connect(self._open_file_dialog)
        self._btn_prev.clicked.connect(self._prev_page)
        self._btn_next.clicked.connect(self._next_page)
        self._page_spin.valueChanged.connect(self._on_spin_changed)
        self._btn_zoom_in.clicked.connect(self._zoom_in)
        self._btn_zoom_out.clicked.connect(self._zoom_out)
        self._btn_fit_width.clicked.connect(self._fit_width)
        self._btn_fit_page.clicked.connect(self._fit_page)

        QShortcut(QKeySequence(Qt.Key_Left),  self).activated.connect(self._prev_page)
        QShortcut(QKeySequence(Qt.Key_Right), self).activated.connect(self._next_page)
        QShortcut(QKeySequence(Qt.Key_Up),    self).activated.connect(self._prev_page)
        QShortcut(QKeySequence(Qt.Key_Down),  self).activated.connect(self._next_page)
        QShortcut(QKeySequence("Ctrl+O"),     self).activated.connect(self._open_file_dialog)
        QShortcut(QKeySequence("Ctrl+="),     self).activated.connect(self._zoom_in)
        QShortcut(QKeySequence("Ctrl+-"),     self).activated.connect(self._zoom_out)
        QShortcut(QKeySequence("Ctrl+0"),     self).activated.connect(self._fit_page)

    # ── Drag-and-drop ─────────────────────────────────────────────────────────

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            paths = [u.toLocalFile() for u in event.mimeData().urls()]
            if paths and paths[0].lower().endswith(".pdf"):
                event.acceptProposedAction()
                return
        event.ignore()

    def dragMoveEvent(self, event) -> None:
        event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        paths = [u.toLocalFile() for u in event.mimeData().urls()]
        if paths:
            event.acceptProposedAction()
            self._load_pdf(paths[0])

    # ── File loading ──────────────────────────────────────────────────────────

    def _open_file_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open PDF", "", "PDF Files (*.pdf)"
        )
        if path:
            self._load_pdf(path)

    def _load_pdf(self, path: str) -> None:
        import fitz
        try:
            doc = fitz.open(path)
            self._page_count = len(doc)
            first = doc[0]
            self._page_width_pts = first.rect.width
            self._page_height_pts = first.rect.height
            doc.close()
        except Exception as e:
            self._set_status(f"Error opening file: {e}")
            return

        self._pdf_path = path
        self._current_page = 0

        self._page_spin.blockSignals(True)
        self._page_spin.setRange(1, self._page_count)
        self._page_spin.setValue(1)
        self._page_spin.blockSignals(False)
        self._page_total.setText(f"/ {self._page_count}")

        self._set_controls_enabled(True)
        self._update_nav_buttons()
        self._fit_width()  # default to fit-width on open

        name = path.replace("\\", "/").split("/")[-1]
        self._set_status(f"{name}  —  {self._page_count} page(s)")

    # ── Navigation ────────────────────────────────────────────────────────────

    def _prev_page(self) -> None:
        if self._current_page > 0:
            self._current_page -= 1
            self._page_spin.blockSignals(True)
            self._page_spin.setValue(self._current_page + 1)
            self._page_spin.blockSignals(False)
            self._update_nav_buttons()
            self._render()

    def _next_page(self) -> None:
        if self._current_page < self._page_count - 1:
            self._current_page += 1
            self._page_spin.blockSignals(True)
            self._page_spin.setValue(self._current_page + 1)
            self._page_spin.blockSignals(False)
            self._update_nav_buttons()
            self._render()

    def _on_spin_changed(self, value: int) -> None:
        if not self._pdf_path:
            return
        self._current_page = value - 1
        self._update_nav_buttons()
        self._render()

    def _update_nav_buttons(self) -> None:
        self._btn_prev.setEnabled(self._current_page > 0)
        self._btn_next.setEnabled(self._current_page < self._page_count - 1)

    # ── Zoom ──────────────────────────────────────────────────────────────────

    def _zoom_in(self) -> None:
        for z in _ZOOM_STEPS:
            if z > self._zoom + 0.01:
                self._set_zoom(z)
                return
        self._set_zoom(_ZOOM_STEPS[-1])

    def _zoom_out(self) -> None:
        for z in reversed(_ZOOM_STEPS):
            if z < self._zoom - 0.01:
                self._set_zoom(z)
                return
        self._set_zoom(_ZOOM_STEPS[0])

    def _fit_width(self) -> None:
        vp_w = self._scroll.viewport().width() - 4
        if self._page_width_pts > 0:
            self._set_zoom(vp_w / self._page_width_pts)

    def _fit_page(self) -> None:
        vp_w = self._scroll.viewport().width() - 4
        vp_h = self._scroll.viewport().height() - 4
        if self._page_width_pts > 0 and self._page_height_pts > 0:
            self._set_zoom(min(vp_w / self._page_width_pts,
                               vp_h / self._page_height_pts))

    def _set_zoom(self, zoom: float) -> None:
        self._zoom = max(_ZOOM_STEPS[0], min(zoom, _ZOOM_STEPS[-1]))
        self._zoom_label.setText(f"{int(round(self._zoom * 100))}%")
        if self._pdf_path:
            self._render()

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.modifiers() & Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self._zoom_in()
            else:
                self._zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)

    # ── Rendering ─────────────────────────────────────────────────────────────

    def _render(self) -> None:
        if not self._pdf_path:
            return

        # If a render is already in flight, queue one more after it finishes
        if self._worker and self._worker.isRunning():
            self._pending_render = True
            return

        self._worker = Worker(
            fn=render_page,
            args=(self._pdf_path, self._current_page, self._zoom)
        )
        self._worker.finished.connect(self._on_render_done)
        self._worker.error.connect(self._on_render_error)
        self._worker.start()

    def _on_render_done(self, data: dict) -> None:
        self._page_width_pts = data["page_width_pts"]
        self._page_height_pts = data["page_height_pts"]

        img = QImage(
            data["samples"],
            data["width"],
            data["height"],
            data["stride"],
            QImage.Format_RGB888,
        )
        pixmap = QPixmap.fromImage(img)
        self._page_view.setPixmap(pixmap)
        self._page_view.resize(pixmap.size())

        if self._pending_render:
            self._pending_render = False
            self._render()

    def _on_render_error(self, msg: str) -> None:
        self._set_status(f"Render error: {msg}")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _set_status(self, text: str) -> None:
        self._status_label.setText(text)

    def _set_controls_enabled(self, enabled: bool) -> None:
        for w in (self._btn_prev, self._btn_next, self._page_spin,
                  self._btn_zoom_in, self._btn_zoom_out,
                  self._btn_fit_width, self._btn_fit_page):
            w.setEnabled(enabled)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        # Re-fit when the panel is resized and a document is open
        if self._pdf_path:
            self._fit_width()
