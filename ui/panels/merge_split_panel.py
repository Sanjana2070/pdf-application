from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget,
    QListWidget, QListWidgetItem, QFileDialog, QWidget,
    QSpinBox, QAbstractItemView
)
from PySide6.QtCore import Qt

from ui.panels.base_panel import BasePanel
from workers.worker import Worker
from services.pdf_service import PdfService


class MergeSplitPanel(BasePanel):

    _accepted_extensions = {".pdf"}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._merge_paths: list[str] = []
        self._split_path: str = ""
        self._worker: Worker | None = None
        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(12)

        title = QLabel("Merge / Split PDF")
        title.setObjectName("panelTitle")

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_merge_tab(), "Merge PDFs")
        self._tabs.addTab(self._build_split_tab(), "Split PDF")

        layout.addWidget(title)
        layout.addWidget(self._tabs, stretch=1)
        layout.addWidget(self._progress_bar)
        layout.addWidget(self._status_label)

    def _build_merge_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self._merge_drop_hint = QLabel("Drag & drop PDF files here, or use Add PDFs")
        self._merge_drop_hint.setObjectName("dropHint")
        self._merge_drop_hint.setAlignment(Qt.AlignCenter)

        self._merge_list = QListWidget()
        self._merge_list.setDragDropMode(QAbstractItemView.InternalMove)
        self._merge_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._merge_list.hide()

        btn_row = QHBoxLayout()
        self._merge_btn_add = QPushButton("Add PDFs")
        self._merge_btn_remove = QPushButton("Remove Selected")
        self._merge_btn_clear = QPushButton("Clear All")
        btn_row.addWidget(self._merge_btn_add)
        btn_row.addWidget(self._merge_btn_remove)
        btn_row.addWidget(self._merge_btn_clear)
        btn_row.addStretch()

        self._merge_btn_run = QPushButton("Merge PDFs")
        self._merge_btn_run.setObjectName("primaryButton")
        self._merge_btn_run.setEnabled(False)

        layout.addWidget(self._merge_drop_hint)
        layout.addWidget(self._merge_list, stretch=1)
        layout.addLayout(btn_row)
        layout.addWidget(self._merge_btn_run)
        return tab

    def _build_split_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self._split_drop_hint = QLabel("Drag & drop a single PDF here, or use Select File")
        self._split_drop_hint.setObjectName("dropHint")
        self._split_drop_hint.setAlignment(Qt.AlignCenter)

        self._split_file_label = QLabel("No file selected.")
        self._split_file_label.setStyleSheet("color: #aaaaaa;")

        self._split_btn_pick = QPushButton("Select PDF File")

        options_row = QHBoxLayout()
        options_row.addWidget(QLabel("Pages per output file:"))
        self._split_pages_spin = QSpinBox()
        self._split_pages_spin.setRange(1, 9999)
        self._split_pages_spin.setValue(1)
        self._split_pages_spin.setFixedWidth(80)
        options_row.addWidget(self._split_pages_spin)
        options_row.addStretch()

        self._split_btn_run = QPushButton("Split PDF")
        self._split_btn_run.setObjectName("primaryButton")
        self._split_btn_run.setEnabled(False)

        layout.addWidget(self._split_drop_hint)
        layout.addWidget(self._split_file_label)
        layout.addWidget(self._split_btn_pick)
        layout.addLayout(options_row)
        layout.addStretch()
        layout.addWidget(self._split_btn_run)
        return tab

    def _connect_signals(self) -> None:
        self._merge_btn_add.clicked.connect(self._merge_pick_files)
        self._merge_btn_remove.clicked.connect(self._merge_remove_selected)
        self._merge_btn_clear.clicked.connect(self._merge_clear)
        self._merge_btn_run.clicked.connect(self._start_merge)
        self._merge_list.model().rowsMoved.connect(self._merge_sync_paths)

        self._split_btn_pick.clicked.connect(self._split_pick_file)
        self._split_btn_run.clicked.connect(self._start_split)

    # ── Drag-and-drop routing ────────────────────────────────────────────────

    def handle_dropped_files(self, paths: list[str]) -> None:
        if self._tabs.currentIndex() == 0:
            self._merge_add_files(paths)
        else:
            if paths:
                self._split_set_file(paths[0])

    # ── Merge helpers ────────────────────────────────────────────────────────

    def _merge_pick_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select PDF Files", "", "PDF Files (*.pdf)"
        )
        if paths:
            self._merge_add_files(paths)

    def _merge_add_files(self, paths: list[str]) -> None:
        for p in paths:
            if p not in self._merge_paths:
                self._merge_paths.append(p)
                name = p.replace("\\", "/").split("/")[-1]
                item = QListWidgetItem(name)
                item.setData(Qt.UserRole, p)
                self._merge_list.addItem(item)
        self._merge_refresh_state()

    def _merge_remove_selected(self) -> None:
        for item in reversed(self._merge_list.selectedItems()):
            self._merge_list.takeItem(self._merge_list.row(item))
        self._merge_sync_paths()

    def _merge_clear(self) -> None:
        self._merge_list.clear()
        self._merge_paths.clear()
        self._merge_refresh_state()

    def _merge_sync_paths(self) -> None:
        self._merge_paths = [
            self._merge_list.item(i).data(Qt.UserRole)
            for i in range(self._merge_list.count())
        ]
        self._merge_refresh_state()

    def _merge_refresh_state(self) -> None:
        has_files = bool(self._merge_paths)
        self._merge_drop_hint.setVisible(not has_files)
        self._merge_list.setVisible(has_files)
        self._merge_btn_run.setEnabled(len(self._merge_paths) >= 2)

    # ── Split helpers ────────────────────────────────────────────────────────

    def _split_pick_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select PDF File", "", "PDF Files (*.pdf)"
        )
        if path:
            self._split_set_file(path)

    def _split_set_file(self, path: str) -> None:
        self._split_path = path
        name = path.replace("\\", "/").split("/")[-1]
        self._split_file_label.setText(f"Selected: {name}")
        self._split_file_label.setStyleSheet("color: #ffffff;")
        self._split_drop_hint.hide()
        self._split_btn_run.setEnabled(True)

    # ── Operations ───────────────────────────────────────────────────────────

    def _start_merge(self) -> None:
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Save Merged PDF As", "merged.pdf", "PDF Files (*.pdf)"
        )
        if not output_path:
            return
        if not output_path.lower().endswith(".pdf"):
            output_path += ".pdf"

        self._set_busy(True)
        self.show_status("")

        self._worker = Worker(
            fn=PdfService.merge_pdfs,
            args=(list(self._merge_paths), output_path)
        )
        self._worker.progress.connect(self.set_progress)
        self._worker.finished.connect(self._on_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _start_split(self) -> None:
        output_dir = QFileDialog.getExistingDirectory(
            self, "Select Output Folder", ""
        )
        if not output_dir:
            return

        self._set_busy(True)
        self.show_status("")

        self._worker = Worker(
            fn=PdfService.split_pdf,
            args=(self._split_path, output_dir, self._split_pages_spin.value())
        )
        self._worker.progress.connect(self.set_progress)
        self._worker.finished.connect(self._on_done)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_done(self, _) -> None:
        self._set_busy(False)
        self.show_status("Done! Files saved successfully.")

    def _on_error(self, msg: str) -> None:
        self._set_busy(False)
        self.show_status(f"Error: {msg}", is_error=True)

    def _set_busy(self, busy: bool) -> None:
        self._merge_btn_run.setEnabled(not busy and len(self._merge_paths) >= 2)
        self._split_btn_run.setEnabled(not busy and bool(self._split_path))
        self._merge_btn_add.setEnabled(not busy)
        self._split_btn_pick.setEnabled(not busy)
        self.show_progress(busy)

    # ── Drag visual feedback ─────────────────────────────────────────────────

    def _on_drag_enter_visual(self) -> None:
        hint = self._merge_drop_hint if self._tabs.currentIndex() == 0 else self._split_drop_hint
        hint.setStyleSheet(
            "color: #0078d4; border: 2px dashed #0078d4; border-radius: 8px; padding: 40px;"
        )

    def _on_drag_leave_visual(self) -> None:
        self._merge_drop_hint.setStyleSheet("")
        self._split_drop_hint.setStyleSheet("")
